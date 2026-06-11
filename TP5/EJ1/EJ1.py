import requests
import sys
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# --------------- CONSTANTES ----------------

HEADERS = {"User-Agent": "Mozilla/5.0"}

# --------------- FUNCIONES ------------------

def obtener_enlaces(url: str = None, proxy=None):
    "Dada una URL, descarga la pagina y obtengo los enlaces. Todos los enlaces estan normalizados"
    try:
        # Descargar la pagina
        response = requests.get(url, headers=HEADERS)
        # print(response)

        # Parser
        soup = BeautifulSoup(response.content, "html.parser")

        links = []

        # Buscar todos los hipervinculos
        for a in soup.find_all("a", href = True):
            href = a.get("href")

            full_url = parse_url(url,href)

            links.append(full_url)

        return links
    except requests.exceptions.RequestException as e:
        print(f"Error al acceder a la URL: {e}")

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

def mostrar_enlaces(links, cant=None):
    "Muestra en pantalla los links, determinada o no una cantidad"
    # print(links)

    print(f"Cantidad de enlaces: {len(links)}")

    # Para marcar el limite de los enlaces
    limite = cant if cant is not None else len(links)

    for link in links[:limite]:
        # Muestro los hrefs
        print(link)


# ------------------- MAIN -----------------

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python EJ1.py <URL>")
    else:
        url = sys.argv[1]
        links = obtener_enlaces(url)

        # Muestro los primeros 5 para probar
        # mostrar_enlaces(links, 5)
        mostrar_enlaces(links)
