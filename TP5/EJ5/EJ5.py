import time
import json
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque, defaultdict
from pyvis.network import Network
from functools import lru_cache
import networkx as nx
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

# --------------- CONSTANTES ----------------

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MiniCrawler/1.0)"}

MAX_PAGINAS = 11  # Cuantas paginas se pueden visitar por dominio
MAX_PROF_LOGICA = 6  # Profundidad maxima del crawler, cuantos saltos desde la semilla
MAX_PROF_FISICA = 6  # Arquitectura de directorios (cantidad de barras de la URL)

DELAY_REQUEST = 0.5
TIMEOUT = 10

URL_SEMILLA = "https://www.unlu.edu.ar"
DOMINIO_OBJETIVO = "unlu.edu.ar"  # Solo se crawlea dentro de este dominio

TOP_K_AUTH = 50
ALPHA_PR   = 0.85
MAX_ITER   = 200
TOL        = 1e-6

# Archivo de caché para no re-crawlear en cada ejecución
CACHE_FILE = "TP5/EJ5/crawl_cache_ej5.json"

OUTPUT_DIR = "TP5/EJ5"

# --------------- FUNCIONES ------------------


def obtener_dominio(url):
    """
    Dada una URL, obtengo su dominio
    Ejemplo: https://www.google.com/search -> www.google.com
    """
    return urlparse(url).netloc


def profundidad_fisica(url):
    """
    Profundidad fisica: cantidad de segmentos de path no vacios (cantidad de barras)
    Ejemplo: https://example.com/a/b/c  ->  3
              https://example.com/  ->  0
    """
    path = urlparse(url).path
    segmentos = [s for s in path.split("/") if s]
    return len(segmentos)


def es_mismo_dominio(url: str, dominio: str) -> bool:
    """
    Verifica si la URL pertenece al dominio objetivo (incluyendo subdominios).
    Ej: 'posgrado.unlu.edu.ar' sigue siendo parte de 'unlu.edu.ar'
    """
    netloc = obtener_dominio(url)
    return netloc == dominio or netloc.endswith("." + dominio)


def normalizar_url(base_url, href):
    """
    Convierte un href relativo en absoluto y descarta fragmentos y
    esquemas no HTTP/HTTPS.
    """
    if not href:
        return None

    # Eliminar fragmento
    if "#" in href:
        href = href.split("#")[0]
    if not href:
        return None

    parsed = urlparse(href)

    # Descartar esquemas que no sean http/https (mailto:, javascript:, etc.)
    if parsed.scheme and parsed.scheme not in ("http", "https"):
        return None

    # Convertir relativa a absoluta
    full = urljoin(base_url, href)

    # Verificar esquema final
    if not full.startswith(("http://", "https://")):
        return None

    return full


@lru_cache
def obtener_pagina(url: str):
    "Descarga una página y devuelve el objeto Response o None si falla."
    try:

        # Descargar la pagina
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        print(f"    [ERROR] {url} -> {e}")
        return None


def extraer_enlaces(url: str, contenido: bytes) -> list[str]:
    "Parsea el HTML y devuelve lista de URLs absolutas normalizadas."

    # Parser
    soup = BeautifulSoup(contenido, "html.parser")
    enlaces = []

    # Buscar todos los hipervinculos
    for a in soup.find_all("a", href=True):
        normalizada = normalizar_url(url, a["href"])  # Normalizo
        if normalizada:
            enlaces.append(normalizada)
    return enlaces


# ---------------- CRAWLER --------------------


def crawler(max_paginas: int = MAX_PAGINAS):
    "Implementa el algoritmo de crawling con una pagina."

    frontier: deque = deque()
    done_list: set[str] = set()
    orden_descubrimiento = []
    grafo_enlaces = {}

    # Semilla: profundidad lógica 0, profundidad física 0
    frontier.append((URL_SEMILLA, 0, profundidad_fisica(URL_SEMILLA)))

    while frontier and len(orden_descubrimiento) < MAX_PAGINAS:
        url, pl, pf = frontier.popleft()

        # ---------- Filtros ----------
        if url in done_list:
            continue
        if not es_mismo_dominio(url, DOMINIO_OBJETIVO):
            continue
        if pl > MAX_PROF_LOGICA:
            continue
        if pf > MAX_PROF_FISICA:
            continue

        n = len(orden_descubrimiento) + 1
        print(f"[{n:>3}/{max_paginas}] PL={pl} PF={pf} | {url}")

        # ---------- Descargar ----------
        response = obtener_pagina(url)
        if response is None:
            done_list.add(url)  # Marcar para no reintentar
            continue

        # Solo procesar respuestas HTML
        content_type = response.headers.get("Content-Type", "")
        if "html" not in content_type:
            done_list.add(url)
            continue

        # ---------- Extraer y encolar enlaces ----------
        orden_descubrimiento.append(url)
        enlaces = extraer_enlaces(url, response.content)

        # Solo guardamos enlaces dentro del dominio
        enlaces_dominio = [l for l in enlaces if es_mismo_dominio(l, DOMINIO_OBJETIVO)]
        grafo_enlaces[url] = enlaces_dominio

        for link in enlaces_dominio:
            if link not in done_list:
                nueva_pf = profundidad_fisica(link)
                nuevo_dominio = obtener_dominio(link)
                actual_dominio = obtener_dominio(url)
                nueva_pl = pl + 1 if nuevo_dominio != actual_dominio else pl
                frontier.append((link, nueva_pl, nueva_pf))

        time.sleep(DELAY_REQUEST)

    print(f"\nCrawling finalizado. Páginas visitadas: {len(orden_descubrimiento)}")
    return orden_descubrimiento, grafo_enlaces


# ----------- CARGAR O CRAWLEAR -------------


def cargar_o_crawlear() -> tuple:
    """
    Si existe el caché, lo carga. Si no, crawlea y guarda el caché.
    Evita tener que re-crawlear cada vez que se ejecuta el script.
    """
    if os.path.exists(CACHE_FILE):
        print(f" Cargando datos desde caché: {CACHE_FILE}")
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data["orden"], data["grafo"]
    else:
        print("No se encontró caché. Iniciando crawling...\n")
        orden, grafo = crawler(MAX_PAGINAS)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({"orden": orden, "grafo": grafo}, f, ensure_ascii=False, indent=2)
        print(f" Datos guardados en caché: {CACHE_FILE}")
        return orden, grafo


# ----------- GRAFO -----------------------


def construir_grafo_nx(orden: list, grafo_enlaces: dict) -> nx.DiGraph:
    """
    Construye un grafo dirigido con NetworkX a partir de las páginas crawleadas.
    Solo se incluyen aristas entre páginas que están en el conjunto crawleado
    (evitar nodos aislados de páginas no visitadas).
    """
    conjunto = set(orden)
    G = nx.DiGraph()
    G.add_nodes_from(orden)

    for origen, destinos in grafo_enlaces.items():
        if origen not in conjunto:
            continue
        for destino in destinos:
            if destino in conjunto and destino != origen:
                G.add_edge(origen, destino)

    print(f"\n Grafo NetworkX construido:")
    print(f"   Nodos : {G.number_of_nodes()}")
    print(f"   Aristas: {G.number_of_edges()}")
    return G


# ----------------- PAGE RANK y HITS --------------------


def calcular_metricas(G: nx.DiGraph) -> tuple:
    """
    Calcula PageRank y Authorities (HITS) para todos los nodos del grafo.
    Devuelve dos dicts: {url: valor}
    ALPHA = 0.85
    MAX_ITER = 100
    """
    print("\nCalculando PageRank...")

    pagerank = nx.pagerank(G, alpha=ALPHA_PR, max_iter=MAX_ITER, tol=TOL)
    print(" PageRank calculado.")

    print("Calculando HITS (Hubs & Authorities)...")
    try:
        hubs, authorities = nx.hits(G, max_iter=MAX_ITER, tol=TOL, normalized=True)
        print("  HITS calculado.")
    except nx.PowerIterationFailedConvergence:
        print("  [WARN] HITS no convergió, usando iteraciones máximas.")
        hubs, authorities = nx.hits(G, max_iter=1000, tol=1e-4, normalized=True)

    return pagerank, authorities, hubs


# --------------------- SIMULACIÓN DE ESTRATEGIA ---------------------

def overlap_acumulado(orden,top_k):
    "% del top-K cubierto al crawlear las primeras i+1 páginas."
    k   = len(top_k)
    enc = 0
    cur = []
    for url in orden:
        if url in top_k:
            enc += 1
        cur.append(enc / k * 100)
    return cur

def simular_estrategia(orden_fifo: list, pagerank: dict, authorities: dict):
    """
    Define y evalúa las estrategias de crawling:
      - FIFO     : orden original de descubrimiento (baseline)
      - PageRank : orden por PageRank descendente
    """

    n = len(orden_fifo)
    k = min(TOP_K_AUTH, n)

    # TOP-K paginas por Authority
    ranking_auth  = sorted(orden_fifo, key=lambda u: authorities.get(u, 0), reverse=True)
    top_k_auth    = set(ranking_auth[:k])

    # Estrategia A: orden por PageRank descendente
    orden_pr      = sorted(orden_fifo, key=lambda u: pagerank.get(u, 0), reverse=True)

    # Estrategia B: FIFO (orden de descubrimiento)
    orden_fifo_cp = list(orden_fifo)

    # Overlaps
    overlap_pr    = overlap_acumulado(orden_pr,      top_k_auth)
    overlap_fifo  = overlap_acumulado(orden_fifo_cp, top_k_auth)
    overlap_ideal = overlap_acumulado(ranking_auth,  top_k_auth) # Curva ideal: si crawleáramos directamente en orden de Authority

    return {
      "n": n, "k": k,
      "top_k_auth":      top_k_auth,
      "ranking_auth":    ranking_auth,
      "orden_pr":        orden_pr,
      "overlap_pr":      overlap_pr,
      "overlap_fifo":    overlap_fifo,
      "overlap_ideal":   overlap_ideal,
    }

# ---------------------- Estadisticas ----------------------

def auc_norm(overlap: list) -> float:
    if not overlap: return 0.0
    return sum(overlap) / (len(overlap) * 100.0)
 
def paginas_para(overlap: list, pct: float) -> int:
    for i, v in enumerate(overlap):
        if v >= pct: return i + 1
    return len(overlap)
 
def etiqueta(url: str, maxlen: int = 60) -> str:
    return url if len(url) <= maxlen else url[:maxlen-3] + "..."
 
def imprimir_reporte(res: dict, pagerank: dict, authorities: dict):
    n, k = res["n"], res["k"]
    print("\n" + "="*62)
    print("  REPORTE DE SIMULACIÓN")
    print("="*62)
    print(f"  Páginas totales : {n}")
    print(f"  Top-K Auth (GT) : {k}")
    print()
 
    for nombre, ov in [("PageRank ↓", res["overlap_pr"]), ("FIFO", res["overlap_fifo"])]:
        print(f"  Estrategia: {nombre}")
        print(f"    AUC normalizada           : {auc_norm(ov):.4f}")
        for p in (25, 50, 75, 100):
            pp = paginas_para(ov, p)
            print(f"    Páginas para cubrir {p:3d}%  : {pp}")
        print()
 
    urls    = list(pagerank)
    pr_v    = [pagerank[u]    for u in urls]
    auth_v  = [authorities[u] for u in urls]
    corr    = np.corrcoef(pr_v, auth_v)[0, 1]
    print(f"  Correlación Pearson PR ↔ Auth : {corr:.4f}")
 
    top_pr   = set(sorted(urls, key=lambda u: pagerank[u],    reverse=True)[:k])
    top_auth = res["top_k_auth"]
    inter    = top_pr & top_auth
    jaccard  = len(inter) / len(top_pr | top_auth) if (top_pr | top_auth) else 0
    print(f"  Overlap top-{k} PR ∩ Auth : {len(inter)} páginas")
    print(f"  Jaccard index             : {jaccard:.4f}")
    print("="*62)
 
    print(f"\n── Top-10 PageRank ──────────────────────────────────")
    for i, u in enumerate(res["orden_pr"][:10], 1):
        print(f"  {i:2d}. {etiqueta(u):<65s}  PR={pagerank[u]:.6f}")
 
    print(f"\n── Top-10 Authority (HITS) ──────────────────────────")
    for i, u in enumerate(res["ranking_auth"][:10], 1):
        print(f"  {i:2d}. {etiqueta(u):<65s}  Auth={authorities[u]:.6f}")

# ------------------- GRAFICOS -------------------------

def graficar_overlap_completo(res: dict, pagerank: dict, authorities: dict,
                               orden_fifo: list, outdir: str):
    """4 subplots: curvas overlap, zoom, top-30 PR, top-30 Auth."""
    n, k        = res["n"], res["k"]
    overlap_pr  = res["overlap_pr"]
    overlap_fifo= res["overlap_fifo"]
    overlap_id  = res["overlap_ideal"]
    xs          = list(range(1, n + 1))
 
    fig = plt.figure(figsize=(18, 12))
    dominio = "unlu.edu.ar"
    fig.suptitle(
        f"Simulación de estrategias de crawling — {dominio}\n"
        f"({n} páginas · Top-{k} por Authority como ground truth)",
        fontsize=14, fontweight="bold", y=0.98
    )
 
    # ── Subplot 1: Overlap completo ──
    ax1 = fig.add_subplot(2, 2, 1)
    ax1.plot(xs, overlap_id,  color="#9e9e9e", lw=1.5, ls=":", label="Ideal (orden Auth)", alpha=0.8)
    ax1.plot(xs, overlap_pr,  color="#ef5350", lw=2,          label="PageRank ↓")
    ax1.plot(xs, overlap_fifo,color="#42a5f5", lw=2,   ls="--",label="FIFO (descubrimiento)")
    for p in (25, 50, 75, 100):
        ax1.axhline(p, color="gray", lw=0.5, ls=":")
    ax1.set_title("Overlap acumulado vs top-K Authority", fontsize=12)
    ax1.set_xlabel("Páginas crawleadas (orden simulado)", fontsize=10)
    ax1.set_ylabel("% del top-K cubierto", fontsize=10)
    ax1.legend(fontsize=9); ax1.set_xlim(1, n); ax1.set_ylim(0, 105)
    ax1.grid(True, ls="--", alpha=0.4)
    auc_pr  = auc_norm(overlap_pr)
    auc_fi  = auc_norm(overlap_fifo)
    ax1.text(0.97, 0.12,
             f"AUC PageRank: {auc_pr:.3f}\nAUC FIFO:     {auc_fi:.3f}",
             transform=ax1.transAxes, ha="right", va="bottom", fontsize=9,
             bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))
 
    # ── Subplot 2: Zoom primeras 150 páginas ──
    ax2 = fig.add_subplot(2, 2, 2)
    zoom = min(150, n)
    ax2.plot(xs[:zoom], overlap_id[:zoom],  color="#9e9e9e", lw=1.5, ls=":", label="Ideal", alpha=0.8)
    ax2.plot(xs[:zoom], overlap_pr[:zoom],  color="#ef5350", lw=2,          label="PageRank ↓")
    ax2.plot(xs[:zoom], overlap_fifo[:zoom],color="#42a5f5", lw=2,   ls="--",label="FIFO")
    for nombre, ov, col in [("PR",   overlap_pr,   "#ef5350"),
                              ("FIFO", overlap_fifo, "#42a5f5")]:
        p50 = paginas_para(ov, 50)
        if p50 <= zoom:
            ax2.axvline(p50, color=col, lw=1, ls="--", alpha=0.6)
            ax2.annotate(f"{nombre}→50%\n@{p50}", xy=(p50, 50),
                         xytext=(p50+3, 38), fontsize=8, color=col)
    ax2.set_title(f"Zoom: primeras {zoom} páginas", fontsize=12)
    ax2.set_xlabel("Páginas crawleadas", fontsize=10)
    ax2.set_ylabel("% del top-K cubierto", fontsize=10)
    ax2.legend(fontsize=9); ax2.set_xlim(1, zoom); ax2.set_ylim(0, 105)
    ax2.grid(True, ls="--", alpha=0.4)
 
    # ── Subplot 3: Top-30 PageRank ──
    ax3   = fig.add_subplot(2, 2, 3)
    top30_pr = sorted(orden_fifo, key=lambda u: pagerank.get(u, 0), reverse=True)[:30]
    vals_pr  = [pagerank[u] for u in top30_pr]
    lbs_pr   = [etiqueta(u, 60) for u in top30_pr]
    cols_pr  = ["#ef5350" if u in res["top_k_auth"] else "#ffcdd2" for u in top30_pr]
    ax3.barh(range(len(top30_pr)), vals_pr, color=cols_pr, edgecolor="white")
    ax3.set_yticks(range(len(top30_pr))); ax3.set_yticklabels(lbs_pr, fontsize=7)
    ax3.invert_yaxis()
    ax3.set_title("Top 30 por PageRank\n(rojo oscuro = también en top-K Auth)", fontsize=11)
    ax3.set_xlabel("PageRank", fontsize=9)
    ax3.xaxis.set_major_formatter(mticker.ScalarFormatter(useMathText=True))
    ax3.grid(axis="x", ls="--", alpha=0.4)
 
    # ── Subplot 4: Top-30 Authority ──
    ax4    = fig.add_subplot(2, 2, 4)
    top30_auth = res["ranking_auth"][:30]
    vals_auth  = [authorities[u] for u in top30_auth]
    lbs_auth   = [etiqueta(u, 60) for u in top30_auth]
    top_pr_set = set(res["orden_pr"][:k])
    cols_auth  = ["#42a5f5" if u in top_pr_set else "#bbdefb" for u in top30_auth]
    ax4.barh(range(len(top30_auth)), vals_auth, color=cols_auth, edgecolor="white")
    ax4.set_yticks(range(len(top30_auth))); ax4.set_yticklabels(lbs_auth, fontsize=7)
    ax4.invert_yaxis()
    ax4.set_title("Top 30 por Authority\n(azul oscuro = también en top-K PageRank)", fontsize=11)
    ax4.set_xlabel("Authority score", fontsize=9)
    ax4.grid(axis="x", ls="--", alpha=0.4)
 
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    out = os.path.join(outdir, "overlap_pagerank_hits.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    print(f"    ✓ Guardado: {out}")
    plt.close()
 
 
def graficar_overlap_simple(res: dict, outdir: str):
    """Gráfico estilo compañero: solo PageRank vs Authority (una curva)."""
    n  = res["n"]
    k  = res["k"]
    xs = list(range(1, n + 1))
 
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(xs, res["overlap_pr"], label="PageRank vs Authority",
            linewidth=2, color="#2196F3")
    ax.set_xlabel("Cantidad de páginas", fontsize=12)
    ax.set_ylabel("Overlap", fontsize=12)
    ax.set_title(f"Evolución del overlap — PageRank vs Authority\n"
                 f"({n} páginas · top-{k} Auth como referencia)", fontsize=13)
    ax.legend(fontsize=11)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f%%"))
    ax.set_ylim(0, 105); ax.set_xlim(1, n)
    ax.grid(True, ls="--", alpha=0.5)
    plt.tight_layout()
    out = os.path.join(outdir, "overlap_simple.png")
    plt.savefig(out, dpi=150)
    print(f"    ✓ Guardado: {out}")
    plt.close()
 
 
def graficar_scatter(pagerank: dict, authorities: dict, outdir: str):
    """Scatter plot de correlación PageRank ↔ Authority."""
    urls   = list(pagerank)
    pr_v   = np.array([pagerank[u]    for u in urls])
    auth_v = np.array([authorities[u] for u in urls])
    corr   = np.corrcoef(pr_v, auth_v)[0, 1]
 
    fig, ax = plt.subplots(figsize=(8, 7))
    ax.scatter(pr_v, auth_v, alpha=0.5, s=20, color="#7b1fa2", edgecolors="none")
 
    # Línea de tendencia
    m, b  = np.polyfit(pr_v, auth_v, 1)
    x_fit = np.linspace(pr_v.min(), pr_v.max(), 200)
    ax.plot(x_fit, m * x_fit + b, color="#d32f2f", lw=1.5, ls="--",
            label=f"Tendencia lineal\nr = {corr:.3f}")
 
    ax.set_xlabel("PageRank", fontsize=12)
    ax.set_ylabel("Authority (HITS)", fontsize=12)
    ax.set_title("Correlación PageRank ↔ Authority", fontsize=13)
    ax.legend(fontsize=11)
    ax.grid(True, ls="--", alpha=0.4)
    plt.tight_layout()
    out = os.path.join(outdir, "scatter_pr_auth.png")
    plt.savefig(out, dpi=150)
    print(f"    ✓ Guardado: {out}")
    plt.close()

# ---------------------- MAIN ----------------------

if __name__ == "__main__":
    print("=" * 60)
    print("  PageRank, HITS y simulación de overlap")
    print("=" * 60)
    print(f"  Dominio  : {DOMINIO_OBJETIVO}")
    print(f"  Páginas  : {MAX_PAGINAS}")
    print(f"  Top-K Auth (ground truth): {TOP_K_AUTH}")
    print("=" * 60 + "\n")

    # Crawlear (o cargar caché)
    orden_fifo, grafo_enlaces = cargar_o_crawlear()

    print(f"\n  Páginas cargadas: {len(orden_fifo)}")

    # Construir grafo NetworkX
    G = construir_grafo_nx(orden_fifo, grafo_enlaces)

    # Calcular métricas
    pagerank, authorities, hubs = calcular_metricas(G)

    # Simular estrategias
    resultados = simular_estrategia(orden_fifo, pagerank, authorities)

    # Reporte en consola
    imprimir_reporte(resultados, pagerank, authorities)

    # Gráficos
    graficar_overlap_completo(resultados, pagerank, authorities, orden_fifo, OUTPUT_DIR)
    graficar_overlap_simple(resultados, OUTPUT_DIR)
    graficar_scatter(pagerank, authorities, OUTPUT_DIR)
