from functools import lru_cache
import time
import requests
import sys
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque, defaultdict
from pyvis.network import Network

# --------------- CONSTANTES ----------------

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MiniCrawler/1.0)"}

MAX_PAGINAS = 1000
MAX_PAGINAS_POR_SITIO = 20 # Cuantas paginas se pueden visitar por dominio
MAX_PROF_LOGICA = 3  # Profundidad maxima del crawler, cuantos saltos desde la semilla
MAX_PROF_FISICA = 3  # Arquitectura de directorios (cantidad de barras de la URL)

DELAY_REQUEST = 1
TIMEOUT = 8

SEMILLA = [
    "https://www.google.com",
    "https://www.youtube.com",
    "https://mail.google.com",
    "https://docs.google.com",
    "https://www.facebook.com",
    "https://outlook.office.com",
    "https://chatgpt.com",
    "https://login.microsoftonline.com",
    "https://outlook.cloud.microsoft",
    "https://accounts.google.com",
    "https://campus-1001.ammon.cloud",
    "https://www.linkedin.com",
    "https://www.bing.com",
    "https://drive.google.com",
    "https://www.instagram.com",
    "https://x.com",
    "https://github.com",
    "https://gemini.google.com",
    "https://calendar.google.com",
    "https://web.whatsapp.com"
]

# SEMILLA = ["https://www.google.com"]

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


# --------------- CRAWLER  ------------------


class Crawler:
    """
    Implementa el algoritmo de crawling con frontier FIFO.

    Cada entrada en la frontier es una tupla:
        (url, dominio_origen, prof_logica, prof_fisica)

    done_list : set de URLs ya visitadas (para no repetir)
    paginas_por_sitio : dict dominio -> cantidad de páginas crawleadas
    grafo : dict url -> lista de urls enlazadas (para armar pyvis)
    """

    def __init__(
        self,
        semilla: list[str],
        max_paginas_por_sitio: int = MAX_PAGINAS_POR_SITIO,
        max_prof_logica: int = MAX_PROF_LOGICA,
        max_prof_fisica: int = MAX_PROF_FISICA,
    ):

        self.max_paginas_por_sitio = max_paginas_por_sitio
        self.max_prof_logica = max_prof_logica
        self.max_prof_fisica = max_prof_fisica

        self.done_list: set[str] = set()
        self.paginas_por_sitio: dict[str, int] = {}
        self.grafo: dict[str, list[str]] = {}  # url_origen -> [url_destino, ...]

        # Frontier: deque usada como cola FIFO
        self.frontier: deque = deque()

        # Inicializar frontier con el conjunto semilla
        for url in semilla:
            dominio = obtener_dominio(url)
            self.frontier.append((url, dominio, 0, 0))
            self.paginas_por_sitio.setdefault(dominio, 0)

    # ---------- Políticas de crawling ----------

    def permite_crawl(
        self, url: str, dominio_origen: str, prof_logica: int, prof_fisica: int
    ) -> bool:
        """
        Devuelve True si la URL puede crawlearse según las políticas definidas.
        """
        dominio = obtener_dominio(url)

        # Ya visitada
        if url in self.done_list:
            return False

        # Profundidad lógica excedida
        if prof_logica > self.max_prof_logica:
            return False

        # Profundidad física excedida
        if prof_fisica > self.max_prof_fisica:
            return False

        # Máximo de páginas por sitio alcanzado
        if self.paginas_por_sitio.get(dominio, 0) >= self.max_paginas_por_sitio:
            return False

        return True

    def calcular_prof_logica(
        self, dominio_origen: str, url_destino: str, prof_logica_actual: int
    ) -> int:
        "La profundidad lógica aumenta cuando se cambia de dominio."

        dominio_destino = obtener_dominio(url_destino)
        if dominio_destino != dominio_origen:
            return prof_logica_actual + 1
        return prof_logica_actual

    # ---------- Crawleo ----------

    def crawl(self):
        "Ejecuta el crawler hasta vaciar la frontier"

        total = 0

        while self.frontier and total < MAX_PAGINAS:
            url, dominio_origen, prof_logica, prof_fisica = self.frontier.popleft()

            if not self.permite_crawl(url, dominio_origen, prof_logica, prof_fisica):
                continue

            dominio = obtener_dominio(url)
            print(f"[{total+1}] Crawling (PL={prof_logica}, PF={prof_fisica}): {url}")

            # Descargar página
            response = obtener_pagina(url)
            if response is None:
                continue

            # Marcar como visitada
            self.done_list.add(url)
            self.paginas_por_sitio[dominio] = self.paginas_por_sitio.get(dominio, 0) + 1
            total += 1

            # Extraer enlaces
            enlaces = extraer_enlaces(url, response.content)
            self.grafo[url] = []

            for link in enlaces:

                # Calcular profundidades del enlace
                nueva_pl = self.calcular_prof_logica(dominio, link, prof_logica)
                nueva_pf = profundidad_fisica(link)

                # Registrar arista en el grafo independientemente de si se va a crawlear
                self.grafo[url].append(link)

                # Agregar a frontier si no fue visitada y no está ya encolada
                if link not in self.done_list:
                    dominio_link = obtener_dominio(link)
                    self.paginas_por_sitio.setdefault(dominio_link, 0)
                    self.frontier.append((link, dominio, nueva_pl, nueva_pf))

            time.sleep(DELAY_REQUEST)

        print(f"\nCrawling finalizado. Páginas visitadas: {total}")
        return total


"""
Algoritmo visto ne clase de crawler
# Frontier: cola FIFO
def crawler(frontier:Queue):
    # Proceso mientras la cola no este vacia
    while not frontier.empty():
        # Recupero URL
        url = frontier.get()
        # Politicas para el crawler
        if permite_crawl(url):
            raw = obtener_enlaces(url)
            # Almaceno el contenido del documento para armar la estructura de datos
            store_document(url,raw.content)
            # Normalizar URLs y meterlas en la cola
            for link in parse_links(raw):
                frontier.put(normalize(link))
"""

# ------------- CONSTRUI GRAFO --------------

def construir_grafo_pyvis(
    grafo: dict[str, list[str]],
    paginas_visitadas: set[str],
    output_file: str = "grafo_crawler.html",
):
    """
    Construye y guarda el grafo de enlaces usando pyvis.
    - Nodos visitados: azul
    - Nodos enlazados pero no visitados: gris
    - Aristas dirigidas: de página origen a página destino
    """
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
      "nodes": {
        "shape": "dot",
        "size": 10,
        "font": { "size": 10 }
      },
      "edges": {
        "arrows": { "to": { "enabled": true, "scaleFactor": 0.5 } },
        "color": { "opacity": 0.5 },
        "smooth": { "type": "dynamic" }
      },
      "physics": {
        "barnesHut": {
          "gravitationalConstant": -8000,
          "springLength": 150
        },
        "stabilization": { "iterations": 100 }
      }
    }
    """)

    nodos_agregados = set()

    def agregar_nodo(url, visitado):
        if url in nodos_agregados:
            return
        dominio = obtener_dominio(url)
        label = dominio  # Etiqueta corta: solo el dominio
        color = "#4fc3f7" if visitado else "#90a4ae"
        titulo = f"<b>{url}</b><br>Dominio: {dominio}<br>{'✓ Visitada' if visitado else '○ No visitada'}"
        net.add_node(
            url, label=label, color=color, title=titulo, size=12 if visitado else 7
        )
        nodos_agregados.add(url)

    # Limitar aristas para legibilidad (máximo 5 por nodo)
    MAX_ARISTAS_POR_NODO = 5

    for origen, destinos in grafo.items():
        agregar_nodo(origen, origen in paginas_visitadas)
        for destino in destinos[:MAX_ARISTAS_POR_NODO]:
            agregar_nodo(destino, destino in paginas_visitadas)
            net.add_edge(origen, destino)

    net.save_graph(output_file)
    print(f"  Grafo guardado en: {output_file}")
    print(f"  Nodos: {len(nodos_agregados)}")
    print(
        f"  Aristas: {sum(min(len(v), MAX_ARISTAS_POR_NODO) for v in grafo.values())}"
    )


# ------------------- MAIN -----------------

if __name__ == "__main__":

    print(" Crawler ")
    print("=" * 60)
    print(f"  Semilla          : {len(SEMILLA)} sitios (top Netcraft)")
    print(f"  Máx. pág/sitio   : {MAX_PAGINAS_POR_SITIO}")
    print(f"  Prof. lógica máx : {MAX_PROF_LOGICA}")
    print(f"  Prof. física máx : {MAX_PROF_FISICA}")
    print("=" * 60)

    crawler = Crawler(
        semilla=SEMILLA,
        max_paginas_por_sitio=MAX_PAGINAS_POR_SITIO,
        max_prof_logica=MAX_PROF_LOGICA,
        max_prof_fisica=MAX_PROF_FISICA,
    )
    
    crawler.crawl()

    # ---------- Estadisticas ----------
    print("\n--- Páginas por dominio ---")
    for dominio, cant in sorted(crawler.paginas_por_sitio.items(),
                                key=lambda x: x[1], reverse=True):
        if cant > 0:
            print(f"  {dominio:<40} {cant} páginas")
 
    # ---------- Grafo ----------
    construir_grafo_pyvis(
        grafo=crawler.grafo,
        paginas_visitadas=crawler.done_list,
        output_file="TP5/EJ2/grafo_crawler.html",
    )
