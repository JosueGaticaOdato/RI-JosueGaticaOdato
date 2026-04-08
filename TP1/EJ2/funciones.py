import string, re

# Eliminacion de acentos a cada palabra
def remover_acentos(palabra):
  # Mapeo palabra con acento a sin acento (las 5 vocales)
  mapeo_acentos = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u'
  }

  # Reemplazo
  for conAcento, sinAcento in mapeo_acentos.items():
    palabra = palabra.replace(conAcento, sinAcento)
  return palabra

# Tokenizer: dado un texto, elimina minusculas, acentos y hace el split
def tokenizer(texto):
  palabras = re.split(r'\W+', texto.lower().strip()) # Split y Minuscula
  # \W : No palabra - + : Uno o mas
  
  palabras = [remover_acentos(palabra) for palabra in palabras] # Elimino acentos

  return [p for p in palabras if p] # Elimino vacios


#print(tokenizer("¡Canción del GATO, árbol!"))

# Contador de tokens
def cantidad_tokens(texto):
  palabras = texto.split(" ")
  return palabras

# Lee el texto y aplica el tokenizar
def procesar_documento(archivo):
    with open(archivo, 'r', encoding='utf-8') as file:
        texto = file.read()
        return tokenizer(texto)

# Lee el texto y cuenta la cantidad de tokens
def procesar_tokens(archivo):
    with open(archivo, 'r', encoding='utf-8') as file:
        texto = file.read()
        return cantidad_tokens(texto)

# Dado un archivo de stopwords, se eliminan todas las palabras vacias dentro de los terminos
def remover_stopwords(terminos,archivo_stopwords):
  with open(archivo_stopwords, 'r', encoding='utf-8') as file:
    stopwords = set(file.read().splitlines())
  return [termino for termino in terminos if termino not in stopwords]
