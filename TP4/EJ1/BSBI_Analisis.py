import argparse
import os
import pickle
from bs4 import BeautifulSoup
from matplotlib import pyplot as plt
import numpy as np

from BSBI import build_index

# ------------ Construccion de indices con N variable ------------

def benchmark(corpus,collection_path, n_values, index_dir, total_docs):
    "Para cada valor de N, correr el algoritmo y registrar tiempos"

    results = []

    for n in n_values:
        pct = n / total_docs * 100
        print(f"\n{'='*55}")
        print(f"  n = {n} docs/bloque ({pct:.0f}% de {total_docs})")
        print(f"{'='*55}")

        #index_path = os.path.join(index_dir, "index.bin")
        #vocab_path = os.path.join(index_dir, "index_vocab.pkl")
        #docmap_path= os.path.join(index_dir, "index_docmap.pkl")
        index_path = os.path.join(index_dir,f"index-{n}")

        os.makedirs(index_path,  exist_ok=True)

        result = build_index(
          corpus=corpus,
          collection_path=collection_path,
          n=n,
          chunks_dir=index_path,
          index_name="index",
        )

        results.append(result)
      
    return results

# Distribucion del tamaño de la posting
def compute_posting_sizes(vocab_path: str) -> np.ndarray:
    """
    Carga el vocabulario y extrae los df de cada término
    """
    with open(vocab_path, "rb") as f:
        vocabulary = pickle.load(f)
    dfs = np.array([v[0] for v in vocabulary.values()], dtype=np.int64)
    return dfs

# -------- Wiki-Small procesamiento (Tomado de TP2/EJ4)  -------------

def extract_text_from_html(filepath:str):
  with open(filepath, "r", encoding="utf-8") as file:
    soup = BeautifulSoup(file,"html.parser")
    return soup.get_text(separator=" ", strip= True)

def process_wiki_collection(root_dir: str) -> dict:
    documents = {}

    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:

            full_path = os.path.join(dirpath, filename)
            relative_path = os.path.relpath(full_path, root_dir)

            try:
                # CASO HTML
                if filename.endswith(".html"):
                    text = extract_text_from_html(full_path)

                # CASO TXT
                elif filename.endswith(".txt"):
                    with open(full_path, "r", encoding="utf-8") as f:
                        text = f.read()

                else:
                    continue

                documents[relative_path] = text

            except Exception as e:
                print(f"Error leyendo {full_path}: {e}")

    return documents

# ------------ GRAFICAS -------------------

def plot_results(results, dfs, output_dir):
    "Grafico de resultados"

    ns       = [r["n"]      for r in results]
    t_idx    = [r["time_index"] for r in results]
    t_mrg    = [r["time_merge"] for r in results]
    t_tot    = [i + m for i, m in zip(t_idx, t_mrg)]
    overhead = [r["overhead"]*100 for r in results]
    chunks   = [r["chunk_count"]  for r in results]

    # 1. Tiempo (indexacion y merge) VS. N
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(ns, t_idx, "o-", label="Indexación", color="#3b82f6", linewidth=2)
    ax.plot(ns, t_mrg, "s-", label="Merge",       color="#f59e0b", linewidth=2)
    ax.plot(ns, t_tot, "^--", label="Total",      color="#6b7280", linewidth=1.5)
    ax.set_xlabel("n  (docs por bloque)")
    ax.set_ylabel("Tiempo (segundos)")
    ax.set_title("Tiempos BSBI en función de n")
    ax.legend()
    ax.grid(True, alpha=0.4)
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "tiempos_vs_n.png"), dpi=150)
    plt.close(fig)
    print(f"Generado tiempos_vs_n.png")

    # 2. Cantidad de chunks VS. N
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar([str(n) for n in ns], chunks, color="#6366f1", edgecolor="white")
    ax.set_xlabel("n  (docs por bloque)")
    ax.set_ylabel("Número de chunks")
    ax.set_title("Chunks generados en función de n")
    ax.grid(True, axis="y", alpha=0.4)
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "chunks_vs_n.png"), dpi=150)
    plt.close(fig)
    print(f"Generado chunks_vs_n.png")

    # 3. Overhead del indice
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(ns, overhead, "D-", color="#ef4444", linewidth=2, markersize=7)
    ax.axhline(y=overhead[-1], linestyle="--", color="#9ca3af", linewidth=1)
    ax.set_xlabel("n  (docs por bloque)")
    ax.set_ylabel("Overhead (%)")
    ax.set_title("Overhead del índice respecto a la colección")
    ax.set_ylim(bottom=0)
    ax.grid(True, alpha=0.4)
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "overhead_vs_n.png"), dpi=150)
    plt.close(fig)
    print(f"Generado overhead_vs_n.png")

    # 4. Tamaño de posting
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.hist(dfs, bins=50, log=True, color="#10b981", edgecolor="white", alpha=0.85)
    ax.set_xlabel("Tamaño de posting list (df)")
    ax.set_ylabel("Número de términos (Log)")
    ax.set_title("Distribución de tamaños de posting lists")
    ax.grid(True, alpha=0.4)
    fig.suptitle(f"Distribución de posting lists  "
                 f"(vocab={len(dfs):,} términos, "
                 f"max_df={dfs.max()})",
                 fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "distribucion_posting_lists.png"), dpi=150)
    print(f"Generado distribucion_posting_lists.png")
    plt.close(fig)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BSBI Indexer")
    parser.add_argument("collection", help="Directorio con los documentos")
    parser.add_argument(
        "--index-dir", default="index/analysis", help="Directorio base para índices"
    )
    args = parser.parse_args()

    collection_path = args.collection
    index_dir = args.index_dir

    # Procesamiento de la coleccion
    print("Procesando coleccion...")
    archivos = sorted(process_wiki_collection(collection_path))

    corpus = [
      (docid, os.path.join(collection_path, archivo))
      for docid, archivo in enumerate(archivos, start=1)
    ]
    total_docs = len(archivos)

    print(f"Colección: {total_docs} documentos en '{collection_path}'")

    # # Valores de N a evaluar
    pcts   = [0.1, 0.2, 0.3, 0.5, 0.6, 0.8, 1]
    n_values = sorted(set(max(1, int(p * total_docs)) for p in pcts))
    print(f"Valores de n a evaluar: {n_values}")

    # Calcular indices y tiempos
    results = benchmark(corpus,collection_path, n_values, index_dir, total_docs)
    #results = 0
    
    # Distribucion de DFs(uso el ultimo n)
    last_n      = n_values[-1]
    last_vocab  = os.path.join(args.index_dir, f"index-{last_n}", "index_vocab.pkl")
    dfs = compute_posting_sizes(last_vocab)

    # Graficos
    plot_results(results, dfs, index_dir)

    print(results)
