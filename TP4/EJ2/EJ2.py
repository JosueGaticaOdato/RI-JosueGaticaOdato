"""
TAAT para Ranking

Consultas:
((t1 AND t2) OR t3)
((t1 AND NOT t2) OR NOT t3)

"""

from abc import ABC, abstractmethod
import argparse
from collections import deque
from enum import Enum
import os
import pickle
import struct

# --------------  CONSTANTES  -------------------

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


# --------------  POSTING LIST  -------------------


class PostingList(ABC):
    """
    API mínima

    Método	      Complejidad	    Descripción

    docid()	      O(1)	          docID actual; None si cursor = −1
    next()	      O(1)	          Avanza el cursor un paso
    weight()	    O(1)	          Peso del documento actual
    ge(d)	        O(?) *	        Avanza hasta el primer docID ≥ d
    reset()	      O(1)	          Reinicia el cursor al inicio

    """

    def __init__(self, docids, freqs=None):
        self._docids = docids
        self._freqs = freqs if freqs else [1] * len(docids)
        self._cursor = 0 if docids else -1

    
    def docid(self):
        """docID actual; None si cursor = -1 (lista agotada)."""
        if self._cursor == -1:
            return None
        return self._docids[self._cursor]

    
    def weight(self):
        """Peso del documento actual."""
        if self._cursor == -1:
            return None
        return float(self._freqs[self._cursor])

    
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


# --------------  OPERADORES BOOLEANOS  -------------------

OPERATORS = {"AND", "OR", "NOT"}


def op_and(p: PostingList, q: PostingList):
    "Intersección de dos posting lists"
    result = []
    while p.docid() is not None and q.docid() is not None:
        if p.docid() == q.docid():
            result.append(p.docid())
            p.next()
            q.next()
        elif p.docid() < q.docid():
            p.next()
        else:
            q.next()
    return result


def op_or(p: PostingList, q: PostingList):
    "Unión de dos posting lists"
    result = []
    while p.docid() is not None and q.docid() is not None:
        if p.docid() == q.docid():
            result.append(p.docid())
            p.next()
            q.next()
        elif p.docid() < q.docid():
            result.append(p.docid())
            p.next()
        else:
            result.append(q.docid())
            q.next()
    # Volcar la lista que no se agotó
    while p.docid() is not None:
        result.append(p.docid())
        p.next()
    while q.docid() is not None:
        result.append(q.docid())
        q.next()
    return result


def op_not(p: PostingList, universe: PostingList):
    """
    NOT p IN universe ≡ universe sin p.
    Para cada docid en universe, lo incluye si NO está en p.
    Los docIDs en q que no están en p.
    """
    result = []
    while universe.docid() is not None:
        curr = universe.docid()
        found_in_p = p.ge(curr)
        if found_in_p != curr:
            result.append(curr)
        universe.next()
    return result


def docids_to_cursor(docids) -> PostingList:
    "Convierte una lista de docids a un cursor (sin frecuencias)."
    return PostingList(sorted(set(docids)))


def tokenize_query(query: str):
    """
    Tokeniza la consulta.
    Ejemplo:

    "((t1 AND NOT t2) OR t3)"
    ["(", "(", "t1", "AND", "NOT", "t2", ")", "OR", "t3", ")"]
    """
    spaced = query.replace("(", " ( ").replace(")", " ) ")
    return spaced.split()


# --------------  EVALUAR  -------------------


def evaluar(query, vocabulario, index_path, docids):
    "Ealua una consulta boolean"

    """Algoritmod de la pila por cada token"
     ( -> Push 
     termino -> Resolver posting
     operador -> Push
     ) -> Evaluar. POP: Operandos y operador. PUSH: Resultado
    """

    tokens = tokenize_query(query)
    stack = deque()
    universe_cursor = PostingList(docids)

    # ---------------------------------------------------

    def obtener_cursor(token):
        "Obtiene el cursor para un término del vocabulario."
        t = token.lower()
        docids, freqs = leer_posting(t, vocabulario, index_path)
        return PostingList(docids, freqs)
    
    # ---------------------------------------------------

    def evaluar_parentesis(frame):
        "Evaluar lo que esta adentro del parentesis"
        i = 0
        resolved = []
        while i < len(frame):
            item = frame[i]
            if item == "NOT":
                # NOT unario: siguiente debe ser un cursor
                i += 1
                operand = frame[i]
                if isinstance(operand, PostingList):
                    universe_cursor.reset()
                    negated = op_not(operand, PostingList(docids))
                    resolved.append(PostingList(negated))
                else:
                    raise ValueError(f"NOT esperaba cursor, encontró: {operand}")
            else:
                resolved.append(item)
            i += 1

        # Ahora resolver AND/OR de izquierda a derecha
        if len(resolved) == 1:
            item = resolved[0]
            if isinstance(item, PostingList):
                docids_r = []
                c = item
                c.reset()
                while c.docid() is not None:
                    docids_r.append(c.docid())
                    c.next()
                return docids_r
            return item  # ya es lista

        # Procesar operadores binarios de izquierda a derecha
        # resolved tiene forma: [cursor, op, cursor, op, cursor, ...]
        left = resolved[0]
        j = 1
        while j < len(resolved):
            op = resolved[j]
            right = resolved[j + 1]

            # Convertir a cursors si son listas
            if isinstance(left, list):
                left = PostingList(left)
            if isinstance(right, list):
                right = PostingList(right)

            left.reset()
            right.reset()

            if op == "AND":
                result_ids = op_and(left, right)
            elif op == "OR":
                result_ids = op_or(left, right)
            else:
                raise ValueError(f"Operador desconocido: {op}")

            left = PostingList(result_ids)
            j += 2

        # Extraer docids del cursor final
        final_ids = []
        left.reset()
        while left.docid() is not None:
            final_ids.append(left.docid())
            left.next()
        return final_ids
    
    # ---------------------------------------------------

    for token in tokens:
        if token == "(":
            stack.append("(")

        elif token == ")":
            # Recolectar el frame entre el "(" correspondiente y ")"
            frame = []
            while stack and stack[-1] != "(":
                frame.insert(0, stack.pop())
            if stack:
                stack.pop()  # quitar el "("
            result_ids = evaluar_parentesis(frame)
            stack.append(PostingList(sorted(result_ids)))

        elif token in OPERATORS:
            stack.append(token)

        else:
            # Es un término
            cursor = obtener_cursor(token)
            stack.append(cursor)

    # Si no hay paréntesis externos, evaluar lo que queda en la pila
    if len(stack) == 1:
        top = stack[0]
        if isinstance(top, PostingList):
            result_ids = []
            top.reset()
            while top.docid() is not None:
                result_ids.append(top.docid())
                top.next()
            return sorted(result_ids)
        return sorted(top) if isinstance(top, list) else []

    # Evaluar frame sin paréntesis (consulta sin envolver)
    remaining = list(stack)
    result_ids = obtener_cursor(remaining)
    return sorted(result_ids)

# # --------------  MOSTRAR RESULTADOS  -------------------

def print_results(result_docids,
                  doc_map,
                  query: str) -> None:
    print(f"\nConsulta : {query}")
    print(f"Resultados: {len(result_docids)} documento(s)")
    print("-" * 45)
    if not result_docids:
        print("  (sin resultados)")
    else:
        print(f"  {'DocName':<30} {'docID':>10}")
        print(f"{'-'*45}")
        for docid in sorted(result_docids):
            name = doc_map.get(docid, f"__doc_{docid}__")
            print(f"  {name:<30} {docid:>6}")
    print("-" * 45)

# # --------------  TAAT  -------------------
# def TAAT(terms, index):
#     acc = {}
#     for term in terms:
#         if term not in index:
#             continue
#         for docid, weight in index[term]:
#             acc[docid] = acc.get(docid, 0) + weight
#     return acc

# --------------  MAIN  -------------------

def main():
    parser = argparse.ArgumentParser(
        description="TAAT Boolean — búsqueda booleana sobre índice BSBI"
    )
    parser.add_argument("query",
        help='Consulta booleana. Ejemplos: '
             '"((t1 AND t2) OR t3)"  '
             '"((t1 AND NOT t2) OR NOT t3)"')
    parser.add_argument("--index-dir",  default="index/debug",
        help="Directorio del índice (default: index/debug)")
    parser.add_argument("--index-name", default="debug_index",
        help="Nombre base del índice (default: debug_index)")
    args = parser.parse_args()

    vocabulary, doc_map = cargar_indice(args.index_dir, args.index_name)
    index_path = os.path.join(args.index_dir, f"{args.index_name}.bin")

    # Universo completo de docids (todos los documentos de la colección)
    all_docids = sorted(doc_map.keys())

    print(f"[TAAT] Vocabulario: {len(vocabulary)} términos | "
          f"Colección: {len(doc_map)} documentos")

    result = evaluar(args.query, vocabulary, index_path, all_docids)
    print_results(result, doc_map, args.query)


if __name__ == "__main__":
    main()
