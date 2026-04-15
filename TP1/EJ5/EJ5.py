import re, os
import time
from nltk.stem import PorterStemmer, LancasterStemmer

# ---------- VARIABLES -----------

# MODIFICAR UBICACION DE LA COLECCION
coleccion = "../Colecciones/vaswani/corpus/doc-text.trec"

base_dir = os.path.dirname(os.path.abspath(__file__))
ruta = os.path.join(base_dir, coleccion)

# --------- FUNCIONES -----------

def parseo_trec(ruta):
  docs = []

  with open(ruta, "r", encoding="utf-8") as file:
    contenido = file.read()

  # Estructura TREC -> <DOC>.....</DOC>
  bloques = re.findall(r"<DOC>(.*?)</DOC>", contenido, re.DOTALL)

  for bloque in bloques:
      b = re.search(r"<DOCNO>(.*?)</DOCNO>", bloque)
      doc = b.group(1).strip() if b else "?"

      texto = re.sub(r"<DOCNO>.*?</DOCNO>", "", bloque, flags=re.DOTALL).strip()

      docs.append((doc, texto))

  return docs

# Todo a lower y solo letras, porque estamos en ingles
def tokenizer(texto):
   return re.findall(r"[a-z]+", texto.lower()) 

def aplicar_stemmer(tokens, stemmer):
  #print(tokens)
  return [stemmer.stem(token) for token in tokens]

# ----------------- MAIN -----------------------

def main():

  # print(ruta)
  # Parseo y tokenizacion
  corpus = parseo_trec(ruta)

  tokens = []
  for doc, texto in corpus:
    tokens.append(tokenizer(texto))
  
  tokens = [token for lista in tokens for token in lista]
  vocabulario = set(tokens)

  print(f"Tokens: {len(tokens)}")
  print(f"Vocabulario: {len(vocabulario)}")

  # Inicializar stemmers
  porter = PorterStemmer()
  lancaster = LancasterStemmer()

  # Medir tiempo de ejecucion y obtener tokens unicos para Porter
  start_porter = time.time()
  porter_tokens = aplicar_stemmer(tokens, porter)
  unicos_porter = set(porter_tokens)
  end_porter = time.time()

  # Medir tiempo de ejecucion y obtener tokens unicos para Lancaster
  start_lancaster = time.time()
  lancaster_tokens = aplicar_stemmer(tokens, lancaster)
  unicos_lancaster = set(lancaster_tokens)
  end_lancaster = time.time()

  with open("resultados.txt", "w", encoding="utf-8") as resultados_file:
    resultados_file.write(
        f"Comparacion de Stemmers: Porter vs. Lancaster\n"
    )
    resultados_file.write(
        f"-----------------------------------------\n"
    )
    resultados_file.write(
        f"Tokens: {len(tokens)}\n"
    )
    resultados_file.write(
        f"Vocabulario: {len(vocabulario)}\n"
    )
    resultados_file.write(
        f"-----------------------------------------\n"
    )
    resultados_file.write(
        f"Cantidad de tokens unicos resultantes:\n"
    )
    resultados_file.write(
        f"Porter: {len(unicos_porter)}\n"
    )
    resultados_file.write(
        f"Lancaster: {len(unicos_lancaster)}\n"
    )
    resultados_file.write(
        f"-----------------------------------------\n"
    )
    resultados_file.write(
        f"Tiempo de ejecucion:\n"
    )
    resultados_file.write(
        f"Porter: {(end_porter - start_porter):.2f} seg.\n"
    )
    resultados_file.write(
        f"Lancaster: {(end_lancaster - start_lancaster):.2f} seg.\n"
    )

  print("Resultados exportados en resultados.txt")


if __name__ == "__main__":
    main()