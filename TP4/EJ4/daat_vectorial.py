"""
DAAT Vectorial — Trabajo Práctico 4
Recuperación de Información — UNLu

Implementa DAAT (Document-At-A-Time) con modelo vectorial TF-IDF
y similitud del coseno sobre el índice construido por bsbi_indexer.py.

Modelo TF-IDF (estándar IR):
  tf(t,d)    = frecuencia bruta del término t en el doc d
  idf(t)     = log₂(N / df(t))        — N = total de documentos
  w(t,d)     = tf(t,d) × idf(t)       — peso del término en el doc
  score(q,d) = coseno(q_vec, d_vec)
             = Σ w(t,q) × w(t,d) / (||q|| × ||d||)

Estrategia DAAT (notebook mTP_4, sección 8):
  1. Cargar posting list de cada término de la consulta
  2. Avanzar todas las listas en paralelo (cursores sincronizados)
  3. En cada paso: tomar el docID mínimo entre todos los cursores
  4. Para ese docID, sumar w(t,d) de todos los términos que lo contienen
  5. Actualizar min-heap de top-k (notebook sección 8 — heapq)
  6. Avanzar los cursores que apuntan a ese docID

Top-k con min-heap (notebook sección 8):
  - top_k = [(score, docid)] de tamaño k
  - Si score_nuevo > top_k[0][0] → heappushpop

Uso:
  python daat_vectorial.py "casa perro" \\
         --index-dir index/debug --index-name debug_index --k 5

  python daat_vectorial.py "the time algorithm" \\
         --index-dir index/analysis/n_200 --index-name index --k 10
"""

import os
import re
import struct
import pickle
import math
import heapq
import argparse
from typing import Dict, List, Optional, Tuple


# ──────────────────────────────────────────────
#  Constantes
# ──────────────────────────────────────────────
LEN_POSTING = 8   # bytes por par (docid, freq)


# ──────────────────────────────────────────────
#  Carga del índice
# ──────────────────────────────────────────────
def load_index(index_dir: str, index_name: str) -> Tuple[Dict, Dict]:
    vocab_path  = os.path.join(index_dir, f"{index_name}_vocab.pkl")
    docmap_path = os.path.join(index_dir, f"{index_name}_docmap.pkl")
    for path, label in [(vocab_path, "vocabulario"), (docmap_path, "doc_map")]:
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"No se encontró {label} en '{path}'. "
                "Ejecutá primero bsbi_indexer.py."
            )
    with open(vocab_path,  "rb") as f: vocabulary = pickle.load(f)
    with open(docmap_path, "rb") as f: doc_map    = pickle.load(f)
    return vocabulary, doc_map


def read_posting(term: str,
                 vocabulary: Dict,
                 index_path: str) -> Tuple[List[int], List[int]]:
    """
    Lee la posting list completa de un término.
    Retorna (docids, freqs) ordenados por docid.
    """
    if term not in vocabulary:
        return [], []
    seek, df, _tid = vocabulary[term]
    with open(index_path, "rb") as f:
        f.seek(seek)
        raw = f.read(df * LEN_POSTING)
    unpacked = struct.unpack(f">{df * 2}I", raw)
    return list(unpacked[0::2]), list(unpacked[1::2])


# ──────────────────────────────────────────────
#  Cursor DAAT con peso TF-IDF
# ──────────────────────────────────────────────
class DaatCursor:
    """
    Cursor para DAAT que encapsula una posting list con su peso TF-IDF.
    Expone:
      docid()  → docID actual o None
      weight() → w(t,d) = tf × idf para el doc actual
      next()   → avanza al siguiente par
      ge(d)    → galloping search hasta docID ≥ d
    """

    def __init__(self, docids: List[int], freqs: List[int], idf: float):
        self._docids = docids
        self._freqs  = freqs
        self._idf    = idf
        self._cursor = 0 if docids else -1

    def docid(self) -> Optional[int]:
        if self._cursor == -1:
            return None
        return self._docids[self._cursor]

    def weight(self) -> float:
        """w(t,d) = tf(t,d) × idf(t)"""
        if self._cursor == -1:
            return 0.0
        return float(self._freqs[self._cursor]) * self._idf

    def idf(self) -> float:
        return self._idf

    def next(self) -> None:
        if self._cursor == -1:
            return
        self._cursor += 1
        if self._cursor >= len(self._docids):
            self._cursor = -1

    def is_exhausted(self) -> bool:
        return self._cursor == -1

    def ge(self, target: int) -> Optional[int]:
        """
        Galloping search: avanza al primer docID ≥ target.
        Fase 1: duplicar salto; Fase 2: búsqueda binaria.
        (notebook mTP_4, sección 5.3)
        """
        if self._cursor == -1:
            return None
        if self._docids[self._cursor] >= target:
            return self._docids[self._cursor]

        lo   = self._cursor
        step = 1
        hi   = lo + step
        while hi < len(self._docids) and self._docids[hi] < target:
            lo    = hi
            step *= 2
            hi    = lo + step
        hi = min(hi, len(self._docids) - 1)

        while lo <= hi:
            mid = (lo + hi) // 2
            if self._docids[mid] == target:
                self._cursor = mid
                return self._docids[mid]
            elif self._docids[mid] < target:
                lo = mid + 1
            else:
                hi = mid - 1

        if lo < len(self._docids):
            self._cursor = lo
            return self._docids[lo]

        self._cursor = -1
        return None

    def __lt__(self, other):
        """Para heap: orden por docid actual."""
        a = self.docid() if self.docid() is not None else float("inf")
        b = other.docid() if other.docid() is not None else float("inf")
        return a < b


# ──────────────────────────────────────────────
#  Cálculo de normas de documentos
# ──────────────────────────────────────────────
def compute_doc_norms(vocabulary: Dict,
                      index_path: str,
                      n_docs:     int) -> Dict[int, float]:
    """
    Precalcula la norma euclidiana de cada documento en el espacio TF-IDF:
      ||d|| = sqrt( Σ_t  (tf(t,d) × idf(t))² )

    Se necesita para normalizar el coseno:
      cosine(q, d) = dot(q, d) / (||q|| × ||d||)
    """
    norms: Dict[int, float] = {}
    N = n_docs

    for term, (seek, df, _tid) in vocabulary.items():
        if df == 0:
            continue
        idf = math.log2(N / df)
        # Leer posting list
        with open(index_path, "rb") as f:
            f.seek(seek)
            raw = f.read(df * LEN_POSTING)
        unpacked = struct.unpack(f">{df * 2}I", raw)
        docids = unpacked[0::2]
        freqs  = unpacked[1::2]
        for docid, freq in zip(docids, freqs):
            w = float(freq) * idf
            norms[docid] = norms.get(docid, 0.0) + w * w

    # Raíz cuadrada
    for docid in norms:
        norms[docid] = math.sqrt(norms[docid])
    return norms


# ──────────────────────────────────────────────
#  DAAT — Document-At-A-Time
# ──────────────────────────────────────────────
def daat_search(query_terms: List[str],
                vocabulary:  Dict,
                index_path:  str,
                n_docs:      int,
                doc_norms:   Dict[int, float],
                k:           int = 10) -> List[Tuple[float, int]]:
    """
    DAAT con similitud coseno TF-IDF.

    Algoritmo (notebook mTP_4, sección 8):
      1. Crear un cursor DaatCursor por cada término de la consulta
         que esté en el vocabulario.
      2. En cada iteración:
         a. Tomar el docID mínimo entre todos los cursores activos.
         b. Para ese docID, sumar w(t,d) de los cursores que lo apuntan.
         c. Calcular score = dot_product / (norm_query × norm_doc).
         d. Actualizar min-heap de top-k.
         e. Avanzar los cursores que apuntaban a ese docID.
      3. Retornar top-k como lista (score, docid) ordenada desc.

    Norma de la consulta:
      ||q|| = sqrt( Σ_t  idf(t)² )
      (tf de cada término de consulta = 1, peso = 1 × idf)

    Parámetros
    ----------
    query_terms : lista de tokens de la consulta (ya normalizados)
    """
    # ── Filtrar términos en vocabulario ───────
    active_terms = [t for t in query_terms if t in vocabulary]
    missing      = [t for t in query_terms if t not in vocabulary]
    if missing:
        print(f"  [DAAT] Términos no encontrados en vocabulario: {missing}")
    if not active_terms:
        print("  [DAAT] Ningún término de la consulta está en el vocabulario.")
        return []

    N = n_docs

    # ── Crear cursores con IDF ─────────────────
    cursors: List[DaatCursor] = []
    query_norm_sq = 0.0
    for term in active_terms:
        _, df, _ = vocabulary[term]
        idf = math.log2(N / df) if df > 0 else 0.0
        docids, freqs = read_posting(term, vocabulary, index_path)
        cursor = DaatCursor(docids, freqs, idf)
        cursors.append(cursor)
        # Peso del término en la consulta: tf_q=1 → w_q(t) = idf(t)
        query_norm_sq += idf * idf

    query_norm = math.sqrt(query_norm_sq) if query_norm_sq > 0 else 1.0

    # ── Top-k con min-heap (notebook sección 8) ───
    # Inicializar con -inf para que cualquier score real (incluso 0) entre
    top_k: List[Tuple[float, int]] = [(-math.inf, -1)] * k
    heapq.heapify(top_k)

    # ── Loop DAAT ─────────────────────────────
    while any(not c.is_exhausted() for c in cursors):
        # Tomar el docID mínimo entre todos los cursores activos
        min_docid = min(
            c.docid() for c in cursors if not c.is_exhausted()
        )

        # Acumular pesos de todos los cursores que apuntan a min_docid
        dot_product = 0.0
        for cursor in cursors:
            if not cursor.is_exhausted() and cursor.docid() == min_docid:
                # w(t,q) = idf(t)  (tf_q = 1)
                # w(t,d) = tf(t,d) × idf(t)
                dot_product += cursor.idf() * cursor.weight()
                cursor.next()

        # Calcular similitud coseno
        d_norm = doc_norms.get(min_docid, 1.0)
        if d_norm > 0 and query_norm > 0:
            score = dot_product / (query_norm * d_norm)
        else:
            score = 0.0

        # Actualizar top-k: si el score supera al mínimo del heap → insertar
        if score > top_k[0][0]:
            heapq.heappushpop(top_k, (score, min_docid))
        elif score == top_k[0][0] and min_docid not in [d for _, d in top_k]:
            # Empate de score: incluir igualmente
            heapq.heappushpop(top_k, (score, min_docid))

    # Ordenar desc por score, excluir entradas ficticias
    results = heapq.nlargest(k, top_k)
    return [(score, docid) for score, docid in results if docid != -1 and score > -1e18]


# ──────────────────────────────────────────────
#  Tokenización de la consulta
# ──────────────────────────────────────────────
def tokenize_query(query: str) -> List[str]:
    """Lowercase + split en tokens alfanuméricos."""
    return re.findall(r"[a-záéíóúñüA-ZÁÉÍÓÚÑÜ]+", query.lower())


# ──────────────────────────────────────────────
#  Salida
# ──────────────────────────────────────────────
def print_results(results: List[Tuple[float, int]],
                  doc_map: Dict,
                  query:   str,
                  k:       int) -> None:
    print(f"\nConsulta : '{query}'")
    print(f"Top-{k} documentos (DAAT, coseno TF-IDF):")
    print("-" * 55)
    if not results:
        print("  (sin resultados)")
    else:
        print(f"  {'DocName':<30} {'docID':>6}  {'Score':>10}")
        print(f"  {'-'*30} {'-'*6}  {'-'*10}")
        for rank, (score, docid) in enumerate(results, 1):
            name = doc_map.get(docid, f"__doc_{docid}__")
            # Formato requerido: DocName:docID:Score
            print(f"  {name:<30} {docid:>6}  {score:>10.6f}")
        print()
        print("  Formato DocName:docID:Score")
        print("  " + "-" * 45)
        for score, docid in results:
            name = doc_map.get(docid, f"__doc_{docid}__")
            print(f"  {name}:{docid}:{score:.6f}")
    print("-" * 55)


# ──────────────────────────────────────────────
#  Entrypoint CLI
# ──────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="DAAT Vectorial — ranking TF-IDF coseno sobre índice BSBI"
    )
    parser.add_argument("query",
        help='Consulta de texto libre. Ejemplo: "casa perro gato"')
    parser.add_argument("--index-dir",  default="index/debug",
        help="Directorio del índice (default: index/debug)")
    parser.add_argument("--index-name", default="debug_index",
        help="Nombre base del índice (default: debug_index)")
    parser.add_argument("-k", "--top-k", type=int, default=10,
        help="Número de documentos a retornar (default: 10)")
    args = parser.parse_args()

    vocabulary, doc_map = load_index(args.index_dir, args.index_name)
    index_path = os.path.join(args.index_dir, f"{args.index_name}.bin")
    n_docs     = len(doc_map)

    print(f"[DAAT] Vocabulario: {len(vocabulary)} términos | "
          f"Colección: {n_docs} documentos")
    print(f"[DAAT] Precalculando normas de documentos...")
    doc_norms = compute_doc_norms(vocabulary, index_path, n_docs)
    print(f"[DAAT] Normas calculadas para {len(doc_norms)} documentos.")

    query_terms = tokenize_query(args.query)
    print(f"[DAAT] Tokens de consulta: {query_terms}")

    results = daat_search(
        query_terms = query_terms,
        vocabulary  = vocabulary,
        index_path  = index_path,
        n_docs      = n_docs,
        doc_norms   = doc_norms,
        k           = args.top_k,
    )

    print_results(results, doc_map, args.query, args.top_k)


if __name__ == "__main__":
    main()
