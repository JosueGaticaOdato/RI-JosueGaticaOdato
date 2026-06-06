"""
TAAT para Modelo Booleano

Consultas:
((t1 AND t2) OR t3)
((t1 AND NOT t2) OR NOT t3)

"""

from abc import ABC
import argparse
from collections import deque
import os
import pickle
import re
import struct
import time

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# --------------  CONSTANTES  -------------------

LEN_POSTING = 8

# -------------- TOKENIZER (del TP1) ----------------------


def tokenizer(texto, stopwords, minimo=2, maximo=float("inf")):
    texto = texto.lower()  # Minusculas

    tokens = re.findall(r"[a-záéíóúüñ]+", texto)  # Solo letras con acento y ñ

    tokens_validos = []
    for token in tokens:

        # Stopwords
        if stopwords and token in stopwords:
            continue

        # Minimo y maximo
        if len(token) > maximo or len(token) < minimo:
            continue

        tokens_validos.append(token)

    return tokens_validos

def read_stopwords(archivo_stopwords):
    with open(archivo_stopwords, "r", encoding="utf-8") as file:
        stopwords = set(file.read().splitlines())
    return stopwords

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

def leer_posting_memoria(term, vocabulario, indice_en_memoria):
    """
    Lee la posting list de un término desde memoria
    """
    df, seek = vocabulario[term]

    # Directamente del buffer en RAM
    raw = indice_en_memoria[seek : seek + (df * LEN_POSTING)]

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

def evaluar(query, vocabulario, index_path, docids, indice_buffer=None):
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

        if indice_buffer is None:
            docids, freqs = leer_posting(t, vocabulario, index_path)
        else:
            docids, freqs = leer_posting_memoria(t, vocabulario, indice_buffer)

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
            # Recolectar el frame entre el "(" y ")"
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

    # Evaluar frame sin paréntesis
    remaining = list(stack)
    result_ids = obtener_cursor(remaining)
    return sorted(result_ids)


# --------------  MOSTRAR RESULTADOS  -------------------

def print_results(result_docids, doc_map, query: str) -> None:
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


# --------------- CARGAR QUERY -----------------------

def load_queries(path, stopwords_path):
    queries = {}
    stopwords_set = read_stopwords(stopwords_path)

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            qid, text = line.split(":", 1)
            queries[int(qid)] = tokenizer(text, stopwords_set)

    # print(queries)
    return queries

# --------------- FILTRAR CANTIDAD DE TERMINOS -----------------------
def filter_by_length(queries, n):
    result = {}

    for q_id, tokens in queries.items():
        if len(tokens) == n:
            result[q_id] = tokens

    return result


def evaluar_querys_dos_terminos(
    querys, vocabulary, index_path, all_docids, docmap, indice_buffer=None
):
    """Evaluamos las querys con la siguiente estrctura
    t1 AND t2
    t1 OR t2
    t1 NOT t2
    """
    resultados = {"AND": [], "OR": [], "NOT": []}

    for qid, tokens in querys.items():
        t1, t2 = tokens[0], tokens[1]

        # Ambos terminos deben estar en el vocabulario
        if t1 not in vocabulary or t2 not in vocabulary:
            continue

        # df de cada termino
        df_t1 = vocabulary[t1][0]
        df_t2 = vocabulary[t2][0]

        # armar query solicitadas
        queries_str = {
            "AND": f"( {t1} AND {t2} )",
            "OR": f"( {t1} OR {t2} )",
            "NOT": f"( {t1} AND NOT {t2} )",
        }

        # Ejecutar y medir tiempo para cada operador
        for op, q_str in queries_str.items():
            t0 = time.perf_counter()
            result = evaluar(q_str, vocabulary, index_path, all_docids, indice_buffer)
            # print_results(result, docmap, q_str)
            tiempo_ejecucion = time.perf_counter() - t0

            resultados[op].append(
                {"qid": qid, "df_t1": df_t1, "df_t2": df_t2, "tiempo": tiempo_ejecucion}
            )

    return resultados


def evaluar_querys_tres_terminos(
    querys, vocabulary, index_path, all_docids, docmap, indice_buffer=None
):
    """Evaluamos las querys con la siguiente estrctura
    t1 AND t2 AND t3
    (t1 OR t2) NOT t3
    (t1 AND t2) OR t3
    """
    resultados = {"AND-AND": [], "OR-AND-NOT": [], "AND-OR": []}

    for qid, tokens in querys.items():
        t1, t2, t3 = tokens[0], tokens[1], tokens[2]

        # Ambos terminos deben estar en el vocabulario
        if t1 not in vocabulary or t2 not in vocabulary or t3 not in vocabulary:
            continue

        # df de cada termino
        df_t1 = vocabulary[t1][0]
        df_t2 = vocabulary[t2][0]
        df_t3 = vocabulary[t3][0]

        # armar query solicitadas
        queries_str = {
            "AND-AND": f"( {t1} AND {t2} AND {t3} )",
            "OR-AND-NOT": f"( ( {t1} OR {t2} ) AND NOT {t3} )",
            "AND-OR": f"( ( {t1} AND {t2} ) OR {t3} )",
        }

        # Ejecutar y medir tiempo para cada operador
        for op, q_str in queries_str.items():
            t0 = time.perf_counter()
            result = evaluar(q_str, vocabulary, index_path, all_docids, indice_buffer)
            # print_results(result, docmap, q_str)
            tiempo_ejecucion = time.perf_counter() - t0

            resultados[op].append(
                {
                    "qid": qid,
                    "df_t1": df_t1,
                    "df_t2": df_t2,
                    "df_t3": df_t3,
                    "tiempo": tiempo_ejecucion,
                }
            )

    return resultados


# ----------------- GRAFICOS ---------------------------


def analizar_resultados(resultados, modo_ejecucion, query_size="2"):
    "Agrupar tiempos y generar graficos relacionados"
    print(f"Generando graficos para modo: {modo_ejecucion}, Query size: {query_size}")

    sns.set_theme(style="whitegrid")
    
    if query_size == "2":
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        fig.suptitle(
            f"Tiempo de Ejecución - Queries Q=2 (Modo: {modo_ejecucion.upper()})",
            fontsize=16,
        )

        # ---------- OR ------------
        if resultados["OR"]:
            df_or = pd.DataFrame(resultados["OR"])
            # la complejidad teórica es la suma de los DF: O(df1 + df2)
            df_or['df_total'] = df_or['df_t1'] + df_or['df_t2']
            
            sns.scatterplot(data=df_or, x='df_total', y='tiempo', ax=axes[0], color='blue', alpha=0.6)
            axes[0].set_title('Operador OR - Tiempo vs (df_1 + df_2)')
            axes[0].set_xlabel('Suma de Frecuencias (df_1 + df_2)')
            axes[0].set_ylabel('Tiempo (segundos)')

        # ---------- AND ----------------
        if resultados["AND"]:
            df_and = pd.DataFrame(resultados["AND"])
            # el tiempo estar limitado por la lista más corta
            df_and['df_min'] = df_and[['df_t1', 'df_t2']].min(axis=1)
            
            sns.scatterplot(data=df_and, x='df_min', y='tiempo', ax=axes[1], color='green', alpha=0.6)
            axes[1].set_title('Operador AND - Tiempo vs min(df_1, df_2)')
            axes[1].set_xlabel('Frecuencia Mínima min(df_1, df_2)')
            axes[1].set_ylabel('Tiempo (segundos)')

        # ---............ NOT ---------
        if resultados["NOT"]:
            df_not = pd.DataFrame(resultados["NOT"])
            
            sns.scatterplot(data=df_not, x='df_t2', y='tiempo', ax=axes[2], color='red', alpha=0.6)
            axes[2].set_title('Operador NOT - Tiempo vs Df_2 (Término negado)')
            axes[2].set_xlabel('Frecuencia del término negado (df_2)')
            axes[2].set_ylabel('Tiempo (segundos)')
    
    else:  # query_size == "3"
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        fig.suptitle(
            f"Tiempo de Ejecución - Queries Q=3 (Modo: {modo_ejecucion.upper()})",
            fontsize=16,
        )

        # ---------- AND-AND --------
        if resultados["AND-AND"]:
            df_and_and = pd.DataFrame(resultados["AND-AND"])
            df_and_and['df_min'] = df_and_and[['df_t1', 'df_t2', 'df_t3']].min(axis=1)
            
            sns.scatterplot(data=df_and_and, x='df_min', y='tiempo', ax=axes[0], color='purple', alpha=0.6)
            axes[0].set_title('Operador AND-AND - Tiempo vs min(df_1, df_2, df_3)')
            axes[0].set_xlabel('Frecuencia Mínima')
            axes[0].set_ylabel('Tiempo (segundos)')

        # ---------- OR-AND-NOT --------
        if resultados["OR-AND-NOT"]:
            df_or_and_not = pd.DataFrame(resultados["OR-AND-NOT"])
            df_or_and_not['df_sum_12'] = df_or_and_not['df_t1'] + df_or_and_not['df_t2']
            
            sns.scatterplot(data=df_or_and_not, x='df_sum_12', y='tiempo', ax=axes[1], color='orange', alpha=0.6)
            axes[1].set_title('Operador (OR)-NOT - Tiempo vs (df_1 + df_2)')
            axes[1].set_xlabel('Suma de Frecuencias (df_1 + df_2)')
            axes[1].set_ylabel('Tiempo (segundos)')

        # ---------- AND-OR --------
        if resultados["AND-OR"]:
            df_and_or = pd.DataFrame(resultados["AND-OR"])
            df_and_or['df_min_12'] = df_and_or[['df_t1', 'df_t2']].min(axis=1)
            
            sns.scatterplot(data=df_and_or, x='df_min_12', y='tiempo', ax=axes[2], color='brown', alpha=0.6)
            axes[2].set_title('Operador (AND)-OR - Tiempo vs min(df_1, df_2)')
            axes[2].set_xlabel('Frecuencia Mínima')
            axes[2].set_ylabel('Tiempo (segundos)')

    plt.tight_layout()
    filename = f"plots-Q{query_size}-{modo_ejecucion.lower()}.png"
    fig.savefig(filename, bbox_inches='tight', dpi=150)
    print(f"Gráfico guardado: {filename}")
    plt.close()


def graficar_comparacion_modos(resultados_disk, resultados_memory, query_size="2"):
    """Generar gráficos comparativos entre disk y memory"""
    print(f"\nGenerando gráficos comparativos para Q={query_size}")
    
    sns.set_theme(style="whitegrid")
    
    if query_size == "2":
        operators = ["AND", "OR", "NOT"]
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        fig.suptitle(
            f"Comparación DISK vs MEMORY - Queries Q=2",
            fontsize=16,
        )
        
        for idx, op in enumerate(operators):
            df_disk = pd.DataFrame(resultados_disk[op])
            df_memory = pd.DataFrame(resultados_memory[op])
            
            if len(df_disk) > 0:
                df_disk['modo'] = 'DISK'
            if len(df_memory) > 0:
                df_memory['modo'] = 'MEMORY'
            
            df_combined = pd.concat([df_disk, df_memory], ignore_index=True)
            
            if len(df_combined) > 0:
                if op == "AND":
                    df_combined['df_metric'] = df_combined[['df_t1', 'df_t2']].min(axis=1)
                    x_label = 'min(df_1, df_2)'
                elif op == "OR":
                    df_combined['df_metric'] = df_combined['df_t1'] + df_combined['df_t2']
                    x_label = 'df_1 + df_2'
                else:  # NOT
                    df_combined['df_metric'] = df_combined['df_t2']
                    x_label = 'df_2 (término negado)'
                
                sns.scatterplot(data=df_combined, x='df_metric', y='tiempo', hue='modo', 
                              ax=axes[idx], alpha=0.6, s=100)
                axes[idx].set_title(f'Operador {op}')
                axes[idx].set_xlabel(x_label)
                axes[idx].set_ylabel('Tiempo (segundos)')
                axes[idx].legend(title='Modo')
    
    else:  # query_size == "3"
        operators = ["AND-AND", "OR-AND-NOT", "AND-OR"]
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        fig.suptitle(
            f"Comparación DISK vs MEMORY - Queries Q=3",
            fontsize=16,
        )
        
        for idx, op in enumerate(operators):
            df_disk = pd.DataFrame(resultados_disk[op])
            df_memory = pd.DataFrame(resultados_memory[op])
            
            if len(df_disk) > 0:
                df_disk['modo'] = 'DISK'
            if len(df_memory) > 0:
                df_memory['modo'] = 'MEMORY'
            
            df_combined = pd.concat([df_disk, df_memory], ignore_index=True)
            
            if len(df_combined) > 0:
                if op == "AND-AND":
                    df_combined['df_metric'] = df_combined[['df_t1', 'df_t2', 'df_t3']].min(axis=1)
                    x_label = 'min(df_1, df_2, df_3)'
                elif op == "OR-AND-NOT":
                    df_combined['df_metric'] = df_combined['df_t1'] + df_combined['df_t2']
                    x_label = 'df_1 + df_2'
                else:  # AND-OR
                    df_combined['df_metric'] = df_combined[['df_t1', 'df_t2']].min(axis=1)
                    x_label = 'min(df_1, df_2)'
                
                sns.scatterplot(data=df_combined, x='df_metric', y='tiempo', hue='modo', 
                              ax=axes[idx], alpha=0.6, s=100)
                axes[idx].set_title(f'Operador {op}')
                axes[idx].set_xlabel(x_label)
                axes[idx].set_ylabel('Tiempo (segundos)')
                axes[idx].legend(title='Modo')
    
    plt.tight_layout()
    filename = f"plots-Q{query_size}-comparacion.png"
    fig.savefig(filename, bbox_inches='tight', dpi=150)
    print(f"Gráfico comparativo guardado: {filename}")
    plt.close()


def imprimir_estadisticas(resultados, query_size="2"):
    """Imprimir estadísticas detalladas de los tiempos"""
    if query_size == "2":
        operators = ["AND", "OR", "NOT"]
    else:
        operators = ["AND-AND", "OR-AND-NOT", "AND-OR"]
    
    print(f"\n{'='*60}")
    print(f"ESTADÍSTICAS - Queries Q={query_size}")
    print(f"{'='*60}")
    
    for op in operators:
        if resultados[op]:
            df_temp = pd.DataFrame(resultados[op])
            print(f"\n{op}:")
            print(f"  Cantidad de queries: {len(df_temp)}")
            print(f"  Tiempo promedio: {df_temp['tiempo'].mean():.6f} segundos")
            print(f"  Tiempo mínimo: {df_temp['tiempo'].min():.6f} segundos")
            print(f"  Tiempo máximo: {df_temp['tiempo'].max():.6f} segundos")
            print(f"  Desv. estándar: {df_temp['tiempo'].std():.6f} segundos")



# # --------------  TAAT de ejemplo  -------------------
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
        description="TAAT Boolean — Ejecucion de querys de 2 y 3 terminos (CON Y SIN MEMORIA)"
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

    args = parser.parse_args()

    vocabulary, doc_map = cargar_indice(args.index_dir, args.index_name)
    index_path = os.path.join(args.index_dir, f"{args.index_name}.bin")

    # Universo completo de docids (todos los documentos de la colección)
    all_docids = sorted(doc_map.keys())

    print(f"\n{'='*70}")
    print(f"[TAAT] EJECUCIÓN CON Y SIN MEMORIA")
    print(f"{'='*70}")
    print(
        f"[TAAT] Vocabulario: {len(vocabulary)} términos | "
        f"Colección: {len(doc_map)} documentos"
    )
    print(f"[TAAT] Índice: {args.index_name}")

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    path_queries = os.path.join(BASE_DIR, "EFF-10K-queries.txt")
    path_stopwords = os.path.join(BASE_DIR, "stopwords.txt")

    queries = load_queries(path_queries, path_stopwords)

    queries_2 = filter_by_length(queries, 2)
    queries_3 = filter_by_length(queries, 3)

    print(f"\nQueries disponibles:")
    print(f"  - Queries con 2 términos: {len(queries_2)}")
    print(f"  - Queries con 3 términos: {len(queries_3)}")

    # ================ EJECUCIÓN SIN MEMORIA (DISK) ================
    print(f"\n{'='*70}")
    print(f"FASE 1: EJECUCIÓN CON ÍNDICE EN DISCO")
    print(f"{'='*70}")

    print(f"\nEjecutando queries Q=2 (DISK)...")
    result_2_disk = evaluar_querys_dos_terminos(
        queries_2, vocabulary, index_path, all_docids, doc_map, indice_buffer=None
    )
    imprimir_estadisticas(result_2_disk, "2")

    print(f"\nEjecutando queries Q=3 (DISK)...")
    result_3_disk = evaluar_querys_tres_terminos(
        queries_3, vocabulary, index_path, all_docids, doc_map, indice_buffer=None
    )
    imprimir_estadisticas(result_3_disk, "3")

    # Generar gráficos individuales para DISK
    analizar_resultados(result_2_disk, "disk", "2")
    analizar_resultados(result_3_disk, "disk", "3")

    # ================ EJECUCIÓN CON MEMORIA (MEMORY) ================
    print(f"\n{'='*70}")
    print(f"FASE 2: EJECUCIÓN CON ÍNDICE EN MEMORIA")
    print(f"{'='*70}")
    print(f"Cargando {args.index_name}.bin en RAM...")
    with open(index_path, "rb") as f:
        indice_buffer = f.read()
    print(f"Índice cargado en memoria ({len(indice_buffer)} bytes)")

    print(f"\nEjecutando queries Q=2 (MEMORY)...")
    result_2_memory = evaluar_querys_dos_terminos(
        queries_2, vocabulary, index_path, all_docids, doc_map, indice_buffer=indice_buffer
    )
    imprimir_estadisticas(result_2_memory, "2")

    print(f"\nEjecutando queries Q=3 (MEMORY)...")
    result_3_memory = evaluar_querys_tres_terminos(
        queries_3, vocabulary, index_path, all_docids, doc_map, indice_buffer=indice_buffer
    )
    imprimir_estadisticas(result_3_memory, "3")

    # Generar gráficos individuales para MEMORY
    analizar_resultados(result_2_memory, "memory", "2")
    analizar_resultados(result_3_memory, "memory", "3")

    # ================ GRÁFICOS COMPARATIVOS ================
    print(f"\n{'='*70}")
    print(f"GENERANDO GRÁFICOS COMPARATIVOS")
    print(f"{'='*70}")
    graficar_comparacion_modos(result_2_disk, result_2_memory, "2")
    graficar_comparacion_modos(result_3_disk, result_3_memory, "3")

    # ================ RESUMEN COMPARATIVO ================
    print(f"\n{'='*70}")
    print(f"RESUMEN: COMPARACIÓN DISK vs MEMORY")
    print(f"{'='*70}")
    
    print(f"\nQUERIES Q=2:")
    for op in ["AND", "OR", "NOT"]:
        if result_2_disk[op] and result_2_memory[op]:
            df_disk = pd.DataFrame(result_2_disk[op])
            df_memory = pd.DataFrame(result_2_memory[op])
            promedio_disk = df_disk['tiempo'].mean()
            promedio_memory = df_memory['tiempo'].mean()
            diferencia = ((promedio_disk - promedio_memory) / promedio_memory) * 100
            print(f"\n  {op}:")
            print(f"    - DISK:   {promedio_disk:.6f} seg (promedio)")
            print(f"    - MEMORY: {promedio_memory:.6f} seg (promedio)")
            print(f"    - Mejora: {abs(diferencia):.2f}% {'más rápido' if diferencia > 0 else 'más lento'} en MEMORY")

    print(f"\nQUERIES Q=3:")
    for op in ["AND-AND", "OR-AND-NOT", "AND-OR"]:
        if result_3_disk[op] and result_3_memory[op]:
            df_disk = pd.DataFrame(result_3_disk[op])
            df_memory = pd.DataFrame(result_3_memory[op])
            promedio_disk = df_disk['tiempo'].mean()
            promedio_memory = df_memory['tiempo'].mean()
            diferencia = ((promedio_disk - promedio_memory) / promedio_memory) * 100
            print(f"\n  {op}:")
            print(f"    - DISK:   {promedio_disk:.6f} seg (promedio)")
            print(f"    - MEMORY: {promedio_memory:.6f} seg (promedio)")
            print(f"    - Mejora: {abs(diferencia):.2f}% {'más rápido' if diferencia > 0 else 'más lento'} en MEMORY")

if __name__ == "__main__":
    main()
