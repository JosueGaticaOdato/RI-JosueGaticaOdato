"""
TAAT vs DAAT sobre Dump10k

Analisis por longitud de query y posting
"""

from collections import defaultdict
import os
import time

from matplotlib import pyplot as plt

# -------------- CARGAR EL INDICE -------------------


def cargar_indice(path):
    "Cargar el indice en base a la coleccion presentada (Dump10K)"
    index = {}

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()  # elimina \n y espacios
            if not line:
                continue

            parts = line.split(":")

            term = parts[0]

            # Tomamos solo los docIDs (tercera parte)
            postings_raw = parts[2].split(",")

            postings = [int(p) for p in postings_raw if p != ""]

            # Ordenar
            postings.sort()

            index[term] = postings

    return index

"""
ALGORITMO Term-At-A-Time (TAAT)

Procesa un término completo a la vez. Para cada término recorre su posting list y acumula el score en un diccionario acc[docid].

Pseudocodigo:
acc = {}
for cada término t en la consulta:
    para cada (docid, weight) en posting_list(t):
        acc[docid] = acc.get(docid, 0) + weight
top_k = nlargest(k, acc)

"""
def taat(query, index):
    "Algoritmo TAAT para recuperacion"
    acc = defaultdict(int)
    for term in query:

        # No me interesa el termino que no este en el indice
        if term not in index:
            continue

        # Recorrer todos los documentos del termino actual
        for doc_id in index[term]:
            acc[doc_id] += 1

    # Ordenar resultados de mayor a menor
    results = sorted(acc.items(), key=lambda item: item[1], reverse=True)
    return results


"""
ALGORITMO Document-At-A-Time (DAAT)

Procesa un documento a la vez en orden de docID. Usa la intersección (binary_merge) para obtener los documentos candidatos y luego suma los pesos de todos los términos para ese documento.

Pseudocodigo:
candidatos = intersección de todas las posting lists
para cada docid en candidatos:
    score = suma de weights de cada posting list para ese docid
    actualizar top-k heap

"""
def daat(query, index):
    "Algoritmo DAAT para recuperación"

    # Filtrar términos que existen
    posting_lists = [index[term] for term in query if term in index]

    if not posting_lists:
        return []

    # Punteros para cada posting empezando en 0
    pointers = [0] * len(posting_lists)
    acc = defaultdict(int)

    while True:
        current_docs = []

        # Obtener doc actual de cada lista
        current_docs = []
        for i, p in enumerate(pointers):
            if p < len(posting_lists[i]):
                current_docs.append(posting_lists[i][p])

        # Si ya no hay más documentos por procesar en ninguna lista, terminamos
        if not current_docs:
            break

        # Evaluar el documento con id mas pequeño
        min_doc = min(current_docs)
        score = 0

        # Avanzar punteros donde coincide con el minimo y sumar al score
        for i in range(len(posting_lists)):
            if (
                pointers[i] < len(posting_lists[i])
                and posting_lists[i][pointers[i]] == min_doc
            ):
                score += 1
                pointers[i] += 1

        acc[min_doc] += score

    # Ordenar resultados
    results = sorted(acc.items(), key=lambda item: item[1], reverse=True)
    return results

# --------------- EVALUAR ALGORITMOS ---------------------------
def evaluar_algoritmos(path_queries, indice):
  stats = defaultdict(lambda: {"count": 0, "taat_time": 0.0, "daat_time": 0.0, "postings": 0}) 
  with open(path_queries, 'r', encoding='utf-8') as f:
    for line in f:
        q_string = line.strip()
        if not q_string:
            continue  # Ignorar líneas en blanco
            
        q_terms = q_string.split()
        len_q = len(q_terms)
        
        # Calcular longitud total de posting lists para esta query
        len_postings = sum(len(indice[t]) for t in q_terms if t in indice)

        # Medir TAAT
        start_taat = time.perf_counter()
        taat(q_terms, indice)
        t_taat = time.perf_counter() - start_taat

        # Medir DAAT
        start_daat = time.perf_counter()
        daat(q_terms, indice)
        t_daat = time.perf_counter() - start_daat

        # Acumular resultados según la longitud de la query
        stats[len_q]["count"] += 1
        stats[len_q]["taat_time"] += t_taat
        stats[len_q]["daat_time"] += t_daat
        stats[len_q]["postings"] += len_postings
  return stats


# -------------- MEDIR TIEMPO DE ALGORITMO -------------------
def medir_tiempo(stats):
  for len_q in sorted(stats.keys()):
    data = stats[len_q]
    count = data["count"]
    
    # Calcular promedios
    avg_postings = data["postings"] / count
    avg_taat = data["taat_time"] / count
    avg_daat = data["daat_time"] / count
    
    
    print(f"{len_q:<15} | {count:<18} | {avg_postings:<18.0f} | {avg_taat:<18.6f} | {avg_daat:<18.6f}")

# -------------- GRAFICOS ---------------------

def graficar(stats):
    lengths = []
    taat_times = []
    daat_times = []
    postings = []
    counts = []

    for len_q in sorted(stats.keys()):
        data = stats[len_q]
        count = data["count"]

        lengths.append(len_q)
        counts.append(count)
        postings.append(data["postings"] / count)
        taat_times.append(data["taat_time"] / count)
        daat_times.append(data["daat_time"] / count)

    # Tiempo vs longitud
    plt.figure()
    plt.plot(lengths, taat_times, marker='o', label="TAAT")
    plt.plot(lengths, daat_times, marker='o', label="DAAT")
    plt.xlabel("Longitud de Query")
    plt.ylabel("Tiempo Promedio (s)")
    plt.title("Tiempo vs Longitud de Query")
    plt.legend()
    plt.grid()
    plt.savefig("grafico1.png", dpi=300, bbox_inches='tight')
    #plt.show()

    # Tiempo vs postings
    plt.figure()
    plt.plot(postings, taat_times, marker='o', label="TAAT")
    plt.plot(postings, daat_times, marker='o', label="DAAT")
    plt.xlabel("Tamaño Promedio Posting List")
    plt.ylabel("Tiempo Promedio (s)")
    plt.title("Tiempo vs Tamaño de Posting")
    plt.legend()
    plt.grid()
    plt.savefig("grafico2.png", dpi=300, bbox_inches='tight')
    #plt.show()

    # Cantidad de queries
    plt.figure()
    plt.bar(lengths, counts)
    plt.xlabel("Longitud de Query")
    plt.ylabel("Cantidad de Queries")
    plt.title("Distribución de Queries")
    plt.savefig("grafico3.png", dpi=300, bbox_inches='tight')
    #plt.show()

def main():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    path_coleccion = os.path.join(BASE_DIR, "../Colecciones/dump10k/dump10k.txt")
    #path_coleccion = os.path.join(BASE_DIR, "../Colecciones/dump10k/test.txt")
    path_queries = os.path.join(BASE_DIR, "queries.txt")


    indice = cargar_indice(path_coleccion)
    #print(indice)

    stats = evaluar_algoritmos(path_queries, indice)

    print(f'{"Long Query":<15} | {"Cantidad":<18} | {"AVG Posting":<18} | {"AVG TIME TAAT":<18} | {"AVG TIME DAAT":<18}')
    medir_tiempo(stats)
    graficar(stats)


if __name__ == "__main__":
    main()
