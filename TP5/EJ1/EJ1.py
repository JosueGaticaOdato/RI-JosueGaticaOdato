import requests
import sys
from bs4 import BeautifulSoup

# --------------- CONSTANTES ----------------

HEADERS = {"User-Agent": "Mozilla/5.0"}

# --------------- FUNCIONES ------------------


def obtener_enlaces(url: str = None, proxy=None):
    "Dada una URL, descarga la pagina y obtengo    los enlaces"
    try:
        # Descargar la pagina
        response = requests.get(url, headers=HEADERS)
        # print(response)

        # Parser
        soup = BeautifulSoup(response.content, "html.parser")

        # Busco todos los hiperlinks
        links = soup.find_all("a")
        return links
    except requests.exceptions.RequestException as e:
        print(f"Error al acceder a la URL: {e}")


def mostrar_enlaces(links, cant=None):
    "Dada una lista de links, meustro sus enlaces"
    # print(links)

    print(f"Cantidad de enlaces: {len(links)}")

    # Para marcar el limite de los enlaces
    limite = cant if cant is not None else len(links)

    for link in links[:limite]:
        # Muestro los hrefs
        print(link.get("href"))


# ------------------- MAIN -----------------

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python EJ1.py <URL>")
    else:
        url = sys.argv[1]
        links = obtener_enlaces(url)

        # Muestro los primeros 5 para probar
        mostrar_enlaces(links, 5)
        # mostrar_enlaces(links)
