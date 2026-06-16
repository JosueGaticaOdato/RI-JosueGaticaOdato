import matplotlib.pyplot as plt
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque, defaultdict
from pyvis.network import Network

# --------------- CONSTANTES ----------------

HEADERS = {
   "User-Agent": "Mozilla/5.0",
}

CANTIDAD_MAXIMA_PAGINAS_POR_SITIO = 50 # Cuantas paginas se pueden visitar por dominio
PROFUNDIDAD_LOGICA_MAXIMA = 2 # Profundidad maxima del crawler, cuantos saltos desde la semilla
PROFUNDIDAD_FISICA_MAXIMA = 2 # Arquitectura de directorios (cantidad de barras de la URL)

BASE_DOMINIO = "https://www.unlu.edu.ar"

# Extensiones a evitar en el sitio acadmemico
EXTENSIONES_EXCLUIDAS = (
    ".pdf", ".jpg", ".png", ".zip", ".doc", ".docx", ".xls", ".xlsx", ".mp4"
)
# --------------- FUNCIONES ------------------

def obtener_enlaces(url: str = None, proxy=None):
    "Dada una URL, descarga la pagina y obtengo los enlaces. Todos los enlaces estan normalizados"
    try:
        # Descargar la pagina
        response = requests.get(url, headers=HEADERS, timeout=5)

        # Parser
        soup = BeautifulSoup(response.content, "html.parser")

        links = []

        # Buscar todos los hipervinculos
        for a in soup.find_all("a", href=True):
          href = a.get("href")

          full_url = parse_url(url, href) # Normalizo

          links.append(full_url)

        return links
    except Exception as e:
        print(f"Error en {url}: {e}")
        return []

def obtener_dominio(url):
    """
    Dada una URL, obtengo su dominio
    Ejemplo: https://www.google.com/search -> www.google.com
    """
    return urlparse(url).netloc

def parse_url(base_url, link):
   "Dada una URL y su link, normalizo el enlace"
   if urlparse(link).fragment: # Si tiene fragmento, descarto
      link = link.split("#")[0]
  
   if urlparse(link).scheme: # URL absoluta, devuelve tal cual
      return link
   
   return urljoin(base_url, link) # Relativa pasa a absoluta

def es_dominio_valido(url):
  "Dada una URL, determina si pertenece o no al dominio base"
  
  if not url:
     return False
  
  dominio = urlparse(url).netloc
  
  # Solo dominio BASE
  if BASE_DOMINIO not in dominio:
     return False
  
  # Evitar archivos pesados
  if url.lower().endswith(EXTENSIONES_EXCLUIDAS):
      return False

  return True

def es_amazon(url):
   "Me dice si la URL pertenece o no a amazon"
   dominio = urlparse(url).netloc
   return "amazon." in dominio

def es_dinamica(url):
    "Determina si una pagina es dinamica"
    parsed = urlparse(url)

    return (
        len(parsed.query) > 0 or
        "?" in url or
        any(x in parsed.path.lower() for x in ["id", "page", "view"])
    )

# profundidad física = cantidad de segmentos en el path
def profundidad_fisica(url):
    "Dada una URL, devuelvo la profundidad fisica"
    path = urlparse(url).path
    if path == "" or path == "/":
        return 0

    return len([p for p in path.split("/") if p])

# ----------------- CRAWLER -----------------

# Frontier: cola FIFO
def crawler(semilla):
    "Genera el corpus de documento dada una semilla de sitios"

    todo_list = deque() # Cola de URLs por visitar
    done_list = set()   # URLs ya visitadas

    # Contador de paginas por dominio
    paginas_por_sitio = defaultdict(int)

    # Grafo dirigido
    # clave = url
    # valor = lista de urls destino
    grafo = defaultdict(list)

    # Estadisticas
    estadisticas = {
        "dinamicas": 0,
        "estaticas": 0,
        "profundidad_logica": defaultdict(int),
        "profundidad_fisica": defaultdict(int),
        "total_urls": 0
    }

    # Inicializado la semilla
    for url in semilla:
       todo_list.append((url,0)) # Profundidad sero porque recien arranco

    # Mientras tenga URLs por recorrer
    while todo_list:
       
      url, profundidad = todo_list.popleft()

      # La salto si ya la visite
      if url in done_list:
         continue
      
      if not es_dominio_valido(url):
        continue
    
      dominio = obtener_dominio(url)

      # Si paso la restriccion de la profundad y la cantidad maxima, salto
      if paginas_por_sitio[dominio] >= CANTIDAD_MAXIMA_PAGINAS_POR_SITIO:
         continue
    
      if profundidad > PROFUNDIDAD_LOGICA_MAXIMA:
         continue

      print(f"[{profundidad}] Crawling: {url}")

      enlaces = obtener_enlaces(url)

      # Agrego a la URL ya visitada y subo el contador del dominio
      done_list.add(url)
      paginas_por_sitio[dominio] += 1

      # --------------- METRICAS ----------------

      estadisticas["total_urls"] += 1

      if es_dinamica(url):
         estadisticas["dinamicas"] += 1
      else:
         estadisticas["estaticas"] += 1
        
      estadisticas["profundidad_logica"][profundidad] += 1

      pf = profundidad_fisica(url)
      estadisticas["profundidad_fisica"][pf] += 1

      # ---------------- GRAFO ---------------

      #print(len(enlaces))
      for link in enlaces:
         
         # Solo links amazon
         if not es_dominio_valido(link):
            continue
         
         # Agrego al grafo
         grafo[url].append(link)

         if link not in done_list:
            # Agrego a la lista con una profundidad mas
            todo_list.append((link,profundidad+1))
    
    return grafo, estadisticas

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

def visualizar_grafo(grafo):
  net = Network(height="800px", width="100%", directed=True)

  for src in grafo:
      net.add_node(src, label=src)

      for dst in grafo[src]:
          net.add_node(dst, label=dst)
          net.add_edge(src, dst)

  #net.show("grafo.html")
  #net.show("grafo.html", notebook=False)
  net.write_html("TP5/EJ2/grafo.html")

# --------------- GRAFICOS ----------------

def armar_graficos(stats):
   
  # Dinamica vs Estatica
  labels = ["Dinámicas", "Estáticas"]
  values = [stats["dinamicas"], stats["estaticas"]]

  plt.figure()
  plt.pie(values, labels=labels, autopct="%1.1f%%")
  plt.title("Distribución de páginas dinámicas vs estáticas")
  plt.savefig("TP5/EJ3/dinamica_vs_estatica.png", dpi=200, bbox_inches="tight")
  plt.close()
  
  # Distribucion por profundidad
  data = stats["profundidad_logica"]

  depths = list(data.keys())
  counts = list(data.values())

  plt.figure()
  plt.bar(depths, counts)
  plt.xlabel("Profundidad")
  plt.ylabel("Cantidad de páginas")
  plt.title("Distribución por profundidad lógica")
  plt.savefig("TP5/EJ3/profundidad.png", dpi=200, bbox_inches="tight")
  plt.close()

  # Histograma de profundiadd
  data = stats["profundidad_logica"]

  values = []
  for profundidad, count in data.items():
      values.extend([profundidad] * count)

  plt.figure()
  plt.hist(values, bins=range(max(values)+2), edgecolor="black")
  plt.xlabel("Profundidad")
  plt.ylabel("Frecuencia")
  plt.title("Histograma de profundidad de crawling")
  plt.savefig("TP5/EJ3/histograma.png", dpi=200, bbox_inches="tight")
  #plt.show()


# ------------------- MAIN -----------------

if __name__ == "__main__":

  semilla = ["https://www.unlu.edu.ar/"]

  grafo, stats = crawler(semilla=semilla)
  
  visualizar_grafo(grafo)

  print("TOTAL URLs:", stats["total_urls"])
  print("DINÁMICAS:", stats["dinamicas"])
  print("ESTÁTICAS:", stats["estaticas"])

  # print("\nProfundidad lógica:")
  # for k, v in sorted(stats["por_profundidad_logica"].items()):
  #     print(k, v)

  # print("\nProfundidad física:")
  # for k, v in sorted(stats["por_profundidad_fisica"].items()):
  #     print(k, v)

  armar_graficos(stats)