from collections import defaultdict
import sys, os, re

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# --------------- FUNCIONES --------------------

# Contador de tokens
def cantidad_tokens(texto, archivo_stopwords, minimo, maximo):
    palabras = texto.split(" ")
    tokens = []
    for palabra in palabras:
        if len(palabra) > maximo or len(palabra) < minimo:
          return
        else:
          tokens.append(palabra)
    return remover_stopwords(tokens, archivo_stopwords)


# Lee el texto y cuenta la cantidad de tokens
def procesar_tokens(archivo, archivo_stopwords, minimo, maximo):
    with open(archivo, "r", encoding="utf-8") as file:
        texto = file.read()
        return cantidad_tokens(texto, archivo_stopwords, minimo, maximo)


# Eliminacion de acentos a cada palabra
def remover_acentos(palabra):
    # Mapeo palabra con acento a sin acento (las 5 vocales)
    mapeo_acentos = {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u"}

    # Reemplazo
    for conAcento, sinAcento in mapeo_acentos.items():
        palabra = palabra.replace(conAcento, sinAcento)
    return palabra


# Tokenizer: dado un texto, elimina minusculas, acentos y hace el split
def tokenizer(texto, archivo_stopwords, minimo, maximo):
    palabras = re.split(r"\W+", texto.lower().strip())  # Split y Minuscula
    # \W : No palabra - + : Uno o mas

    palabras = [remover_acentos(palabra) for palabra in palabras]  # Elimino acentos
    palabras = [p for p in palabras if p] # Elimino vacios

    validas = []
    for palabra in palabras:
        if len(palabra) > maximo or len(palabra) < minimo:
          return
        else:
          validas.append(palabra)
    validas = remover_stopwords(validas, archivo_stopwords)

    return validas 


# Lee el texto y aplica el tokenizar
def procesar_documento(archivo, archivo_stopwords, minimo, maximo):
    with open(archivo, "r", encoding="utf-8") as file:
        texto = file.read()
        return tokenizer(texto, archivo_stopwords, minimo, maximo)


# Dado un archivo de stopwords, se eliminan todas las palabras vacias dentro de los terminos
def remover_stopwords(terminos, archivo_stopwords):
    if (not archivo_stopwords):
        return
    with open(archivo_stopwords, "r", encoding="utf-8") as file:
        stopwords = set(file.read().splitlines())
    return [termino for termino in terminos if termino not in stopwords]


# -----------------------------------------------------

# ---------------- ANALIZADOR LEXICO ------------------

LONGITUD_MINIMA = 2 
LONGITUD_MAXIMA = 23 #Palabra mas largo del diccionario https://www.elmundo.es/como/2023/06/19/649052cdfdddff8a4f8b4578.html

def analizador_lexico(
    directorio, minimo, maximo, archivo_stopwords=None
):

    # --------- DEFINICION DE VARIBLES -------------

    # TF y DF
    tf = defaultdict(int)  # Frecuencia de termino
    df = defaultdict(int)  # Frecuencia de documento

    # Contador tokens, terminos y cantidad de terminos que aparecen 1 vez en la coleccion
    contador_token = 0
    contador_termino = 0
    terminos_unavez = 0

    # Cantidad de tokens y terminos del documento mas corto y mas largo
    nombre_documentoMasCorto = ""
    tokens_doc_mas_corto = 0
    terminos_doc_mas_corto = float("inf")
    
    nombre_documentoMasLargo = ""
    tokens_doc_mas_largo = 0
    terminos_doc_mas_largo = 0

    # Largo promedio de un termino
    letras_totales_terminos = 0

    # --------- LECTURA DE ARCHIVOS ---------------

    for archivo in os.listdir(directorio):
        if archivo.endswith(".txt"):
            path = os.path.join(directorio, archivo)

            # --------- ANALISIS LEXICO ---------------

            tokens = procesar_tokens(path, archivo_stopwords, minimo, maximo)
            terminos = procesar_documento(path , archivo_stopwords, minimo, maximo)

            contador_token += len(tokens)

            # Obtencion del documento mas largo y mas corto
            contador_termino += len(set(terminos))

            cantidad_tokens = len(tokens)
            cantidad_terminos = len(terminos)
            
            if cantidad_terminos < terminos_doc_mas_corto:
                terminos_doc_mas_corto = cantidad_terminos
                tokens_doc_mas_corto = cantidad_tokens
                nombre_documentoMasCorto = archivo
            
            if cantidad_terminos > terminos_doc_mas_largo:
                terminos_doc_mas_largo = cantidad_terminos
                tokens_doc_mas_largo = cantidad_tokens
                nombre_documentoMasLargo = archivo

            # Manejamos TF y DF:
            for termino in terminos:
              tf[termino] += 1  # Cuantas veces aparece cada termino en toda la coleccion

            for termino in set(terminos):
              df[termino] += 1  # Cuantos documentos aparece cada termino

    # Ordenar de mayor a menor frecuencia
    terminos_ordenados = sorted(tf.items(), key=lambda x: x[1], reverse=True)
    for termino, frecuencia in tf.items():
        if frecuencia == 1:
            terminos_unavez += 1

    # --------- ESTADISTICAS -------------

    promedio_token_documento = contador_token / len(os.listdir(directorio))
    promedio_termino_documento = contador_termino / len(os.listdir(directorio))

    # --------- TERMINO.TXT -------------

    with open("terminos.txt", "w", encoding="utf-8") as terminos_file:
        for termino, cf in terminos_ordenados:
            letras_totales_terminos += len(termino)
            terminos_file.write(f"{termino} {cf} {df[termino]}\n")

    # --------- ESTADISTICAS.TXT -------------

    with open("estadisticas.txt", "w", encoding="utf-8") as estadisticas_file:
        estadisticas_file.write(f"{len(os.listdir(directorio))}\n")
        estadisticas_file.write(f"{contador_token} {len(terminos_ordenados)}\n")
        estadisticas_file.write(f"{promedio_token_documento:.2f} {promedio_termino_documento:.2f}\n")
        estadisticas_file.write(f"{(letras_totales_terminos/len(terminos_ordenados)):.2f}\n")
        estadisticas_file.write(f"{nombre_documentoMasCorto} {tokens_doc_mas_corto} {terminos_doc_mas_corto}\n")
        estadisticas_file.write(f"{nombre_documentoMasLargo} {tokens_doc_mas_largo} {terminos_doc_mas_largo}\n")
        estadisticas_file.write(f"{terminos_unavez}\n")

    # --------- FRECUENCIAS.TXT -------------

    with open("frecuencias.txt", "w", encoding="utf-8") as frecuencias_file:
        frecuencias_file.write(
            "Los 10 terminos mas frecuentes y su CF (Collection Frequency):\n"
        )
        for termino, frecuencia in terminos_ordenados[:10]:
            frecuencias_file.write(f"{termino} {frecuencia}\n")

        frecuencias_file.write(
            "\nLos 10 terminos menos frecuentes y su CF (Collection Frequency):\n"
        )
        for termino, frecuencia in terminos_ordenados[-10:]:
            frecuencias_file.write(f"{termino} {frecuencia}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python EJ2.py <directorio> [Opc: <archivo_stopwords>]")
        sys.exit(1)

    directorio = sys.argv[1]
    archivo_stopwords = sys.argv[2] if len(sys.argv) > 2 else None

    analizador_lexico(directorio, archivo_stopwords, LONGITUD_MINIMA, LONGITUD_MAXIMA)

    print("Analizador lexico realizado, archivos .txt exportados.")
