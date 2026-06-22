import time

import matplotlib.pyplot as plt
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque, defaultdict
from pyvis.network import Network
from functools import lru_cache

# --------------- CONSTANTES ----------------

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MiniCrawler/1.0)"}

MAX_PAGINAS = 200  # Cuantas paginas se pueden visitar por dominio
MAX_PROF_LOGICA = 3  # Profundidad maxima del crawler, cuantos saltos desde la semilla
MAX_PROF_FISICA = 3  # Arquitectura de directorios (cantidad de barras de la URL)

DELAY_REQUEST = 0.5
TIMEOUT = 10

URL_SEMILLA = "https://www.unlu.edu.ar"
DOMINIO_OBJETIVO = "unlu.edu.ar"  # Solo se crawlea dentro de este dominio

# Extensiones de pagina dinamica
EXT_DINAMICAS = {
    ".php",
    ".asp",
    ".aspx",
    ".jsp",
    ".cgi",
    ".cfm",
    ".do",
    ".action",
    ".py",
}

# Extensiones de pagina estatica
EXT_ESTATICAS_NO_HTML = {
    ".html",
    ".htm",
    ".shtml",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".svg",
    ".ico",
    ".webp",
    ".css",
    ".js",
    ".xml",
    ".txt",
    ".csv",
    ".zip",
    ".rar",
    ".mp3",
    ".mp4",
    ".avi",
    ".mov",
}

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


def clasificar_pagina(url: str) -> str:
    """
    Clasifica una URL como 'dinamica' o 'estatica'.

    Criterios:
    - Dinámica: tiene query string (?) O la extensión del path es dinámica
    - Estática: todo lo demás (HTML puro, sin query string, recursos estáticos)
    """
    parsed = urlparse(url)

    # Query string presente, entonces es dinámica
    if parsed.query:
        return "dinamica"

    # Analizar extensión del path
    path = parsed.path.rstrip("/")
    if "." in path.split("/")[-1]:
        ext = "." + path.split(".")[-1].lower()
        if ext in EXT_DINAMICAS:
            return "dinamica"

    return "estatica"


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


# -------- REGISTRO DE LA PAGINA --------------


class InfoPagina:
    "Datos recolectados de una página crawleada."

    def __init__(self, url: str, prof_logica: int, prof_fisica: int):
        self.url = url
        self.prof_logica = prof_logica
        self.prof_fisica = prof_fisica
        self.tipo = clasificar_pagina(url)  # 'dinamica' | 'estatica'

    def __repr__(self):
        return (
            f"InfoPagina(url={self.url!r}, PL={self.prof_logica}, "
            f"PF={self.prof_fisica}, tipo={self.tipo!r})"
        )


# ---------------- CRAWLER --------------------


def crawler():
    "Implementa el algoritmo de crawling con una pagina."

    frontier: deque = deque()
    done_list: set[str] = set()
    grafo: dict[str, list[str]] = {}
    paginas_info: list[InfoPagina] = []

    # Semilla: profundidad lógica 0, profundidad física 0
    frontier.append((URL_SEMILLA, 0, profundidad_fisica(URL_SEMILLA)))

    total = 0

    while frontier and total < MAX_PAGINAS:
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

        # ---------- Descargar ----------
        print(f"[{total+1:>3}] PL={pl} PF={pf} | {url}")
        response = obtener_pagina(url)
        if response is None:
            done_list.add(url)  # Marcar para no reintentar
            continue

        # Solo procesar respuestas HTML
        content_type = response.headers.get("Content-Type", "")
        if "html" not in content_type:
            done_list.add(url)
            continue

        # ---------- Registrar ----------
        done_list.add(url)
        total += 1
        paginas_info.append(InfoPagina(url, pl, pf))

        # ---------- Extraer y encolar enlaces ----------
        enlaces = extraer_enlaces(url, response.content)
        grafo[url] = []

        for link in enlaces:
            if not es_mismo_dominio(link, DOMINIO_OBJETIVO):
                continue
            grafo[url].append(link)
            if link not in done_list:
                nueva_pf = profundidad_fisica(link)
                nuevo_dominio = obtener_dominio(link)
                actual_dominio = obtener_dominio(url)
                nueva_pl = pl + 1 if nuevo_dominio != actual_dominio else pl
                frontier.append((link, nueva_pl, nueva_pf))

        time.sleep(DELAY_REQUEST)

    print(f"\nCrawling finalizado. Páginas visitadas: {total}")
    return paginas_info, grafo


# --------------- GRAFICOS ----------------


def analizar_y_graficar(paginas: list[InfoPagina]):
    """
    Genera y muestra tres gráficos:
      1. Torta: distribución dinámicas vs estáticas
      2. Barras: frecuencia por profundidad lógica
      3. Barras: frecuencia por profundidad física
    """
    if not paginas:
        print("No hay páginas para analizar.")
        return

    # -------- Conteos --------
    n_dinamicas = sum(1 for p in paginas if p.tipo == "dinamica")
    n_estaticas = sum(1 for p in paginas if p.tipo == "estatica")

    dist_pl: dict[int, int] = defaultdict(int)
    dist_pf: dict[int, int] = defaultdict(int)
    for p in paginas:
        dist_pl[p.prof_logica] += 1
        dist_pf[p.prof_fisica] += 1

    # -------- Imprimir resumen --------
    total = len(paginas)
    print("\n" + "=" * 50)
    print("  ANÁLISIS DE RESULTADOS")
    print("=" * 50)
    print(f"  Total de páginas crawleadas : {total}")
    print(
        f"  Dinámicas                   : {n_dinamicas} ({n_dinamicas/total*100:.1f}%)"
    )
    print(
        f"  Estáticas                   : {n_estaticas} ({n_estaticas/total*100:.1f}%)"
    )
    print()
    print("  Distribución por Profundidad Lógica:")
    for nivel in sorted(dist_pl):
        print(f"    PL={nivel} : {dist_pl[nivel]} páginas")
    print()
    print("  Distribución por Profundidad Física:")
    for nivel in sorted(dist_pf):
        print(f"    PF={nivel} : {dist_pf[nivel]} páginas")
    print("=" * 50)

    # -------- Figura con 3 subplots --------
    fig, axes = plt.subplots(1, 3, figsize=(16, 6))
    fig.suptitle(
        f"Análisis del crawling de {DOMINIO_OBJETIVO}\n({total} páginas)",
        fontsize=14,
        fontweight="bold",
    )

    # -- 1. Torta dinámicas vs estáticas --
    ax1 = axes[0]
    labels = ["Dinámicas", "Estáticas"]
    valores = [n_dinamicas, n_estaticas]
    colores = ["#ef5350", "#42a5f5"]
    explode = (0.05, 0.05)

    # Evitar torta vacía si uno de los valores es 0
    if all(v == 0 for v in valores):
        ax1.text(0.5, 0.5, "Sin datos", ha="center", va="center")
    else:
        wedges, texts, autotexts = ax1.pie(
            valores,
            labels=labels,
            colors=colores,
            autopct="%1.1f%%",
            explode=explode,
            startangle=90,
            textprops={"fontsize": 11},
        )
        for at in autotexts:
            at.set_fontsize(11)
            at.set_fontweight("bold")

    ax1.set_title("Páginas Dinámicas vs Estáticas", fontsize=12, pad=15)

    # -- 2. Barras profundidad lógica --
    ax2 = axes[1]
    niveles_pl = sorted(dist_pl.keys())
    counts_pl = [dist_pl[n] for n in niveles_pl]

    bars2 = ax2.bar(
        [str(n) for n in niveles_pl],
        counts_pl,
        color="#66bb6a",
        edgecolor="white",
        linewidth=0.8,
    )
    ax2.bar_label(bars2, padding=3, fontsize=10, fontweight="bold")
    ax2.set_title("Distribución por Profundidad Lógica", fontsize=12)
    ax2.set_xlabel("Profundidad Lógica", fontsize=11)
    ax2.set_ylabel("Cantidad de páginas", fontsize=11)
    ax2.set_ylim(0, max(counts_pl, default=1) * 1.2)
    ax2.grid(axis="y", linestyle="--", alpha=0.5)

    # -- 3. Barras profundidad física --
    ax3 = axes[2]
    niveles_pf = sorted(dist_pf.keys())
    counts_pf = [dist_pf[n] for n in niveles_pf]

    bars3 = ax3.bar(
        [str(n) for n in niveles_pf],
        counts_pf,
        color="#ffa726",
        edgecolor="white",
        linewidth=0.8,
    )
    ax3.bar_label(bars3, padding=3, fontsize=10, fontweight="bold")
    ax3.set_title("Distribución por Profundidad Física", fontsize=12)
    ax3.set_xlabel("Profundidad Física", fontsize=11)
    ax3.set_ylabel("Cantidad de páginas", fontsize=11)
    ax3.set_ylim(0, max(counts_pf, default=1) * 1.2)
    ax3.grid(axis="y", linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig("TP5/EJ3/analisis_ej3.png", dpi=150, bbox_inches="tight")
    #print("\n Gráfico guardado en: analisis_unlu.png")


# ------------- Pyvis ----------------------


def construir_grafo_pyvis(
    grafo: dict[str, list[str]],
    paginas_info: list[InfoPagina],
    output_file: str = "grafo_unlu.html",
):
    """
    Genera el grafo de enlace interno de unlu.edu.ar con pyvis.
    Color según tipo: azul=estática, rojo=dinámica
    """
    try:
        from pyvis.network import Network
    except ImportError:
        print("pyvis no instalado. Saltando generación de grafo.")
        return

    tipo_map = {p.url: p.tipo for p in paginas_info}

    net = Network(
        height="800px",
        width="100%",
        directed=True,
        bgcolor="#1a1a2e",
        font_color="white",
        notebook=False,
    )
    net.set_options("""
    {
      "nodes": { "shape": "dot", "size": 8, "font": { "size": 9 } },
      "edges": {
        "arrows": { "to": { "enabled": true, "scaleFactor": 0.4 } },
        "color": { "opacity": 0.4 },
        "smooth": { "type": "dynamic" }
      },
      "physics": {
        "barnesHut": { "gravitationalConstant": -6000, "springLength": 120 },
        "stabilization": { "iterations": 80 }
      }
    }
    """)

    nodos = set()
    MAX_DEST = 5  # aristas por nodo para legibilidad

    def add_node(url):
        if url in nodos:
            return
        tipo = tipo_map.get(url, "estatica")
        color = "#ef5350" if tipo == "dinamica" else "#42a5f5"
        label = urlparse(url).path[:30] or "/"
        net.add_node(url, label=label, color=color, title=f"{url}<br>Tipo: {tipo}")
        nodos.add(url)

    for origen, destinos in grafo.items():
        add_node(origen)
        for dest in destinos[:MAX_DEST]:
            add_node(dest)
            net.add_edge(origen, dest)

    net.save_graph(output_file)
    print(f"  Grafo guardado en: {output_file}")
    print(f"  Nodos: {len(nodos)}")


# ------------------- MAIN -----------------

if __name__ == "__main__":
    print("  CRAWLER unlu.edu.ar ")
    print("=" * 60)
    print(f"  Dominio objetivo   : {DOMINIO_OBJETIVO}")
    print(f"  Máx. páginas       : {MAX_PAGINAS}")
    print(f"  Prof. lógica máx   : {MAX_PROF_LOGICA}")
    print(f"  Prof. física máx   : {MAX_PROF_FISICA}")
    print("=" * 60 + "\n")

    paginas, grafo = crawler()
 
    analizar_y_graficar(paginas)
 
    construir_grafo_pyvis(grafo, paginas, output_file="TP5/EJ3/grafo_unlu.html")