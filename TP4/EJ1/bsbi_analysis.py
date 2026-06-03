"""
BSBI Analysis — Trabajo Práctico 4
Recuperación de Información — UNLu

Ejecuta el indexador BSBI con distintos valores de n,
registra tiempos por separado (indexación y merge),
grafica la distribución de tamaños de posting lists
y calcula el overhead del índice.

Uso:
    python bsbi_analysis.py --collection <dir> --index-dir <dir>
"""

import os
import sys
import pickle
import struct
import time
import shutil
import argparse
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

# Importar las funciones del indexer
sys.path.insert(0, os.path.dirname(__file__))
from bsbi_indexer import bsbi_index, bsbi_merge, LEN_POSTING


# ─────────────────────────────────────────────
#  Benchmark con distintos valores de n
# ─────────────────────────────────────────────
def benchmark(collection_path: str,
              n_values: list,
              base_chunks_dir: str,
              base_index_dir:  str) -> list:
    """
    Para cada valor de n en n_values, corre BSBI completo
    y registra tiempos de indexación y merge por separado.

    Retorna lista de dicts con los resultados.
    """
    results = []
    total_docs = len([f for f in os.listdir(collection_path)
                      if not f.startswith(".")])

    for n in n_values:
        pct = n / total_docs * 100
        print(f"\n{'='*55}")
        print(f"  n = {n} docs/bloque ({pct:.0f}% de {total_docs})")
        print(f"{'='*55}")

        chunks_dir = os.path.join(base_chunks_dir, f"n_{n}")
        index_dir  = os.path.join(base_index_dir,  f"n_{n}")
        index_path = os.path.join(index_dir, "index.bin")
        vocab_path = os.path.join(index_dir, "index_vocab.pkl")
        docmap_path= os.path.join(index_dir, "index_docmap.pkl")

        os.makedirs(chunks_dir, exist_ok=True)
        os.makedirs(index_dir,  exist_ok=True)

        # Fase 1: indexación
        term2id, doc_map, chunk_count, t_index = bsbi_index(
            collection_path, n, chunks_dir
        )

        # Fase 2: merge
        vocabulary, t_merge = bsbi_merge(
            term2id, chunk_count, chunks_dir,
            index_path, vocab_path, docmap_path, doc_map
        )

        # Tamaños
        col_size   = sum(
            os.path.getsize(os.path.join(collection_path, f))
            for f in os.listdir(collection_path)
            if not f.startswith(".")
        )
        idx_size   = os.path.getsize(index_path)  if os.path.exists(index_path)  else 0
        vocab_size = os.path.getsize(vocab_path)  if os.path.exists(vocab_path)  else 0
        chunks_size= sum(
            os.path.getsize(os.path.join(chunks_dir, f))
            for f in os.listdir(chunks_dir)
        )

        overhead = (idx_size + vocab_size) / col_size if col_size else 0

        results.append({
            "n":            n,
            "pct":          pct,
            "chunks":       chunk_count,
            "vocab_size":   len(vocabulary),
            "t_index":      t_index,
            "t_merge":      t_merge,
            "t_total":      t_index + t_merge,
            "col_size_kb":  col_size   / 1024,
            "idx_size_kb":  idx_size   / 1024,
            "vocab_size_kb":vocab_size / 1024,
            "chunks_size_kb":chunks_size / 1024,
            "overhead":     overhead,
        })

        print(f"  chunks={chunk_count} | vocab={len(vocabulary)} | "
              f"t_idx={t_index:.3f}s | t_merge={t_merge:.3f}s | "
              f"overhead={overhead*100:.1f}%")

    return results


# ─────────────────────────────────────────────
#  Distribución de tamaños de posting lists
# ─────────────────────────────────────────────
def compute_posting_sizes(vocab_path: str) -> np.ndarray:
    """
    Carga el vocabulario y extrae los df (document frequency)
    de cada término → distribución de tamaños de posting lists.
    """
    with open(vocab_path, "rb") as f:
        vocabulary = pickle.load(f)
    dfs = np.array([v[1] for v in vocabulary.values()], dtype=np.int64)
    return dfs


# ─────────────────────────────────────────────
#  Gráficos
# ─────────────────────────────────────────────
def plot_results(results: list,
                 dfs:     np.ndarray,
                 output_dir: str) -> None:
    """Genera y guarda todos los gráficos del análisis."""
    os.makedirs(output_dir, exist_ok=True)

    ns       = [r["n"]      for r in results]
    t_idx    = [r["t_index"] for r in results]
    t_mrg    = [r["t_merge"] for r in results]
    t_tot    = [r["t_total"] for r in results]
    overhead = [r["overhead"]*100 for r in results]
    chunks   = [r["chunks"]  for r in results]

    # ── 1. Tiempos de indexación y merge vs n ──
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
    print(f"  → tiempos_vs_n.png")

    # ── 2. Número de chunks vs n ──────────────
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar([str(n) for n in ns], chunks, color="#6366f1", edgecolor="white")
    ax.set_xlabel("n  (docs por bloque)")
    ax.set_ylabel("Número de chunks")
    ax.set_title("Chunks generados en función de n")
    ax.grid(True, axis="y", alpha=0.4)
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "chunks_vs_n.png"), dpi=150)
    plt.close(fig)
    print(f"  → chunks_vs_n.png")

    # ── 3. Distribución de tamaños de posting lists (log-log) ──
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Histograma lineal
    ax = axes[0]
    ax.hist(dfs, bins=50, color="#10b981", edgecolor="white", alpha=0.85)
    ax.set_xlabel("Tamaño de posting list (df)")
    ax.set_ylabel("Número de términos")
    ax.set_title("Distribución de tamaños de posting lists")
    ax.grid(True, alpha=0.4)

    # Histograma log-log
    ax = axes[1]
    log_bins = np.logspace(np.log10(max(1, dfs.min())),
                           np.log10(dfs.max()), 40)
    ax.hist(dfs, bins=log_bins, color="#8b5cf6", edgecolor="white", alpha=0.85)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Tamaño de posting list (df) — escala log")
    ax.set_ylabel("Número de términos — escala log")
    ax.set_title("Distribución (escala log-log) — Ley de Zipf")
    ax.grid(True, which="both", alpha=0.3)

    fig.suptitle(f"Distribución de posting lists  "
                 f"(vocab={len(dfs):,} términos, "
                 f"max_df={dfs.max()}, mediana={int(np.median(dfs))})",
                 fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "distribucion_posting_lists.png"), dpi=150)
    plt.close(fig)
    print(f"  → distribucion_posting_lists.png")

    # ── 4. Overhead del índice ────────────────
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
    print(f"  → overhead_vs_n.png")

    # ── 5. Tabla resumen (texto) ──────────────
    print("\n" + "=" * 75)
    print(f"{'n':>6} {'%col':>6} {'chunks':>7} {'t_idx(s)':>10} "
          f"{'t_mrg(s)':>10} {'t_tot(s)':>10} {'overhead':>10}")
    print("-" * 75)
    for r in results:
        print(f"{r['n']:>6} {r['pct']:>5.0f}% {r['chunks']:>7} "
              f"{r['t_index']:>10.4f} {r['t_merge']:>10.4f} "
              f"{r['t_total']:>10.4f} {r['overhead']*100:>9.1f}%")
    print("=" * 75)

    # ── 6. Estadísticas de posting lists ──────
    print("\nEstadísticas de posting lists:")
    print(f"  Términos (vocab)   : {len(dfs):,}")
    print(f"  df mínimo          : {dfs.min()}")
    print(f"  df máximo          : {dfs.max()}")
    print(f"  df mediana         : {np.median(dfs):.0f}")
    print(f"  df promedio        : {dfs.mean():.2f}")
    print(f"  df std             : {dfs.std():.2f}")
    print(f"  Términos con df=1  : {(dfs==1).sum():,} ({(dfs==1).mean()*100:.1f}%)")
    print(f"  Términos con df>10 : {(dfs>10).sum():,} ({(dfs>10).mean()*100:.1f}%)")


# ─────────────────────────────────────────────
#  Entrypoint
# ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Análisis BSBI con múltiples valores de n"
    )
    parser.add_argument("--collection",
                        default="collection/wiki",
                        help="Directorio de la colección")
    parser.add_argument("--index-dir",
                        default="index/analysis",
                        help="Directorio base para índices")
    parser.add_argument("--chunks-dir",
                        default="chunks/analysis",
                        help="Directorio base para chunks")
    parser.add_argument("--output-dir",
                        default="plots",
                        help="Directorio para guardar gráficos")
    args = parser.parse_args()

    collection_path = args.collection
    if not os.path.isdir(collection_path):
        print(f"Error: directorio de colección no encontrado: '{collection_path}'")
        return

    total_docs = len([f for f in os.listdir(collection_path)
                      if not f.startswith(".")])
    print(f"Colección: {total_docs} documentos en '{collection_path}'")

    # Valores de n: 10%, 20%, 30%, 50%, 100% del total
    pcts   = [0.10, 0.20, 0.30, 0.50, 1.00]
    n_vals = sorted(set(max(1, int(p * total_docs)) for p in pcts))
    print(f"Valores de n a evaluar: {n_vals}")

    # Benchmark
    results = benchmark(
        collection_path  = collection_path,
        n_values         = n_vals,
        base_chunks_dir  = args.chunks_dir,
        base_index_dir   = args.index_dir,
    )

    # Calcular distribución de posting lists usando el último n (colección completa)
    last_n      = n_vals[-1]
    last_vocab  = os.path.join(args.index_dir, f"n_{last_n}", "index_vocab.pkl")
    dfs = compute_posting_sizes(last_vocab)

    # Gráficos
    print(f"\nGenerando gráficos en '{args.output_dir}'...")
    plot_results(results, dfs, args.output_dir)
    print("\n¡Análisis completo!")


if __name__ == "__main__":
    main()
