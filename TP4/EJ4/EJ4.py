"""
DAAT para Ranking

Consultas con modelo vectorial utilizando metrica del coseno

"""

# --------------  CONSTANTES  -------------------

import argparse
import heapq
import math
import os
import pickle
import re
import struct
from typing import Dict, List, Tuple

LEN_POSTING = 8

# --------------  FUNCIONES  -------------------


def cargar_indice(index_dir, index_name):
    "Cargar vocabulario y doc_map desde disco"
    vocab_path = os.path.join(index_dir, f"{index_name}_vocab.pkl")
    docmap_path = os.path.join(index_dir, f"{index_name}_docmap.pkl")
    for path, label in [(vocab_path, "vocabulario"), (docmap_path, "doc_map")]:
        if not os.path.exists(path):
            raise FileNotFoundError(f"No se encontró {label} en '{path}'. ")
    with open(vocab_path, "rb") as f:
        vocabulary = pickle.load(f)
    with open(docmap_path, "rb") as f:
        doc_map = pickle.load(f)
    return vocabulary, doc_map


def leer_posting(term, vocabulario, index_path):
    """
    Lee la posting list de un término desde disco
    """
    if term not in vocabulario:
        return [], []

    df, seek = vocabulario[term]
    with open(index_path, "rb") as f:
        f.seek(seek)
        raw = f.read(df * LEN_POSTING)

    unpacked = struct.unpack(f">{df * 2}I", raw)
    docids = list(unpacked[0::2])
    freqs = list(unpacked[1::2])
    return docids, freqs


# --------------  POSTING LIST (para DAAT con TF-IDF)  -------------------


class DaatCursor:
    """
    API mínima

    Método	      Complejidad	    Descripción

    docid()	      O(1)	          docID actual; None si cursor = −1
    next()	      O(1)	          Avanza el cursor un paso
    weight()	    O(1)	          Peso del documento actual
    ge(d)	        O(log(?)) *	    Avanza hasta el primer docID ≥ d
    reset()	      O(1)	          Reinicia el cursor al inicio

    """

    def __init__(self, docids, freqs, idf):
        self._docids = docids
        self._freqs = freqs
        self._idf = idf
        self._cursor = 0 if docids else -1

    def docid(self):
        """docID actual; None si cursor = -1 (lista agotada)."""
        if self._cursor == -1:
            return None
        return self._docids[self._cursor]

    def weight(self):
        """Peso del documento actual.
        w = tf x idf
        """
        if self._cursor == -1:
            return 0.0
        return float(self._freqs[self._cursor]) * self._idf

    def idf(self):
        return self._idf

    def next(self) -> None:
        """Avanza al siguiente documento. Cursor → -1 si no hay más."""
        if self._cursor == -1:
            return
        self._cursor += 1
        if self._cursor >= len(self._docids):
            self._cursor = -1

    def ge(self, target) -> int:
        "Galloping search"

        if self._cursor == -1:
            return None
        if self._docids[self._cursor] >= target:
            return self._docids[self._cursor]

        # Fase 1galloping: duplicar el salto
        lo = self._cursor
        step = 1
        hi = lo + step
        while hi < len(self._docids) and self._docids[hi] < target:
            lo = hi
            step *= 2
            hi = lo + step
        hi = min(hi, len(self._docids) - 1)

        # Fase 2 búsqueda binaria en [lo, hi]
        while lo <= hi:
            mid = (lo + hi) // 2
            if self._docids[mid] == target:
                self._cursor = mid
                return self._docids[mid]
            elif self._docids[mid] < target:
                lo = mid + 1
            else:
                hi = mid - 1

        # target no existe: posicionar en el primer elemento > target
        if lo < len(self._docids):
            self._cursor = lo
            return self._docids[lo]

        self._cursor = -1
        return None

    def reset(self):
        """Reinicia el cursor al inicio de la lista."""
        self._cursor = 0 if self._docids else -1

    def is_exhausted(self):
        return self._cursor == -1

    def __repr__(self):
        return (
            f"PostingList(docid={self.docid()}, "
            f"len={len(self._docids)}, cursor={self._cursor})"
        )


# ------------ CALCULO DE NORMA ---------------------


def calcular_norma_documentos(vocabulary, index_path, n_docs):
    """
    Precalcula la norma euclidiana de cada documento en el espacio TF-IDF:
      ||d|| = sqrt( Σ_t  (tf(t,d) × idf(t))² )

    Se necesita para normalizar el coseno:
      cosine(q, d) = dot(q, d) / (||q|| × ||d||)
    """
    norms: Dict[int, float] = {}
    N = n_docs

    #print(vocabulary.items())

    for term, (df, seek) in vocabulary.items():
        if df == 0:
            continue
        idf = math.log2(N / df)
        # Leer posting list
        with open(index_path, "rb") as f:
            f.seek(seek)
            raw = f.read(df * LEN_POSTING)
        unpacked = struct.unpack(f">{df * 2}I", raw)
        docids = unpacked[0::2]
        freqs = unpacked[1::2]
        for docid, freq in zip(docids, freqs):
            w = float(freq) * idf
            norms[docid] = norms.get(docid, 0.0) + w * w

    # Raíz cuadrada
    for docid in norms:
        norms[docid] = math.sqrt(norms[docid])

    return norms


# --------------- DAAT --------------------------


def daat_busqueda(query_terms, vocabulary, index_path, n_docs, doc_norms, k=10):
    """
    DAAT con similitud coseno TF-IDF

    Algoritmo :
      1. Crear un cursor por cada término de la consulta que esté en el vocabulario.
      2. En cada iteración:
         a. Tomar el docID mínimo entre todos los cursores activos.
         b. Para ese docID, sumar w(t,d) de los cursores que lo apuntan.
         c. Calcular score = dot_product / (norm_query × norm_doc).
         d. Actualizar min-heap de top-k.
         e. Avanzar los cursores que apuntaban a ese docID.
      3. Retornar top-k como lista (score, docid) ordenada desc.

    Norma de la consulta:
      ||q|| = sqrt( Σ_t  idf(t)² )

    Parámetros
    ----------
    query_terms : lista de tokens de la consulta (ya normalizados)
    """

    # Filtrar terminos del vocabulario
    active_terms = [t for t in query_terms if t in vocabulary]
    missing = [t for t in query_terms if t not in vocabulary]
    if missing:
        #print(f"  [DAAT] Términos no encontrados en vocabulario: {missing}")
        pass
    if not active_terms:
        #print("  [DAAT] Ningún término de la consulta está en el vocabulario.")
        return []

    N = n_docs

    # Crear cursores
    cursors: List[DaatCursor] = []
    query_norm_sq = 0.0
    for term in active_terms:
        #print(vocabulary[term])
        df, _ = vocabulary[term]
        idf = math.log2(N / df) if df > 0 else 0.0
        docids, freqs = leer_posting(term, vocabulary, index_path)
        cursor = DaatCursor(docids, freqs, idf)
        cursors.append(cursor)
        # Peso del término en la consulta: tf_q=1 → w_q(t) = idf(t)
        query_norm_sq += idf * idf

    query_norm = math.sqrt(query_norm_sq) if query_norm_sq > 0 else 1.0

    # Top-k con min-heap
    # Inicializar con -inf para que cualquier score real entre
    top_k: List[Tuple[float, int]] = [(-math.inf, -1)] * k
    heapq.heapify(top_k)

    # Algoritmo DAAT
    while any(not c.is_exhausted() for c in cursors):
        # Tomar el docID mínimo entre todos los cursores activos
        min_docid = min(c.docid() for c in cursors if not c.is_exhausted())

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

        # Actualizar top-k: si el score supera al mínimo del heap, entonces inserto
        if score > top_k[0][0]:
            heapq.heappushpop(top_k, (score, min_docid))
        elif score == top_k[0][0] and min_docid not in [d for _, d in top_k]:
            # Empate de score: incluir igualmente
            heapq.heappushpop(top_k, (score, min_docid))

    # Ordenar desc por score, excluir entradas ficticias
    results = heapq.nlargest(k, top_k)
    return [(score, docid) for score, docid in results if docid != -1 and score > -1e18]


def tokenize_query(query: str) -> List[str]:
    """Lowercase + split en tokens alfanuméricos."""
    return re.findall(r"[a-záéíóúñüA-ZÁÉÍÓÚÑÜ]+", query.lower())


# --------------  MOSTRAR RESULTADOS  -------------------


def print_results(results, doc_map, query, k):
    #print(f"\nConsulta : '{query}'")
    #print(f"Top-{k} documentos (DAAT, coseno TF-IDF):")
    #print("-" * 45)
    if not results:
        print("  (sin resultados)")
    else:
        #print(f"  {'DocName':<30} {'docID':>6}  {'Score':>10}")
        #print(f"  {'-'*30} {'-'*6}  {'-'*10}")
        for rank, (score, docid) in enumerate(results, 1):
            name = doc_map.get(docid, f"__doc_{docid}__")
            # Formato requerido: DocName:docID:Score
            #print(f"  {name:<30} {docid:>6}  {score:>10.6f}")
        #print()
        #print("  Formato DocName:docID:Score")
        #print("  " + "-" * 45)
        for score, docid in results:
            name = doc_map.get(docid, f"__doc_{docid}__")
            print(f"  {name}:{docid}:{score:.6f}")
    #print("-" * 45)


# --------------  MAIN  -------------------


def main():
    parser = argparse.ArgumentParser(
        description="DAAT Vectorial — ranking TF-IDF coseno sobre índice BSBI"
    )
    parser.add_argument(
        "query", help='Consulta de texto libre. Ejemplo: "casa perro gato"'
    )
    parser.add_argument(
        "--index-dir",
        default="index/debug",
        help="Directorio del índice (default: index/debug)",
    )
    parser.add_argument(
        "--index-name",
        default="debug_index",
        help="Nombre base del índice (default: debug_index)",
    )
    parser.add_argument(
        "-k",
        "--top-k",
        type=int,
        default=10,
        help="Número de documentos a retornar (default: 10)",
    )
    args = parser.parse_args()

    vocabulary, doc_map = cargar_indice(args.index_dir, args.index_name)
    index_path = os.path.join(args.index_dir, f"{args.index_name}.bin")
    n_docs = len(doc_map)

    # print(
    #     f"[DAAT] Vocabulario: {len(vocabulary)} términos | "
    #     f"Colección: {n_docs} documentos"
    # )
    # print(f"[DAAT] Precalculando normas de documentos...")
    doc_norms = calcular_norma_documentos(vocabulary, index_path, n_docs)
    #print(f"[DAAT] Normas calculadas para {len(doc_norms)} documentos.")

    query_terms = tokenize_query(args.query)
    # print(f"[DAAT] Tokens de consulta: {query_terms}")

    results = daat_busqueda(
        query_terms=query_terms,
        vocabulary=vocabulary,
        index_path=index_path,
        n_docs=n_docs,
        doc_norms=doc_norms,
        k=args.top_k,
    )

    print_results(results, doc_map, args.query, args.top_k)


if __name__ == "__main__":
    main()
