from collections import defaultdict
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from funciones import procesar_documento, remover_stopwords, stemming

def analizador_lexico(
    directorio, archivo_stopwords=None, minimo=1, maximo=float("inf")
):

    # --------- DEFINICION DE VARIBLES -------------

    # TF y DF
    tf = defaultdict(int)  # Frecuencia de termino
    df = defaultdict(int)  # Frecuencia de documento

    # --------- LECTURA DE ARCHIVOS ---------------

    for archivo in os.listdir(directorio):
        if archivo.endswith(".txt"):
            path = os.path.join(directorio, archivo)

            # --------- ANALISIS LEXICO ---------------

            terminos = procesar_documento(path)

            # Eliminamos palabras vacias si existen
            if archivo_stopwords:
                terminos = remover_stopwords(terminos, archivo_stopwords)

            # Aplico Stemming
            terminos = stemming(terminos)

            # Manejamos TF y DF:
            for termino in terminos:
                if minimo <= len(termino) <= maximo:
                    tf[
                        termino
                    ] += 1  # Cuantas veces aparece cada termino en toda la coleccion

            for termino in set(terminos):
                if minimo <= len(termino) <= maximo:
                    df[termino] += 1  # Cuantos documentos aparece cada termino

    # Ordenar de mayor a menor frecuencia
    terminos_ordenados = sorted(tf.items(), key=lambda x: x[1], reverse=True)

    # --------- TERMINO-STEMMMING.TXT -------------

    with open("terminos-stemming.txt", "w", encoding="utf-8") as terminos_file:
        for termino, cf in terminos_ordenados:
            terminos_file.write(f"{termino} {cf} {df[termino]}\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python EJ4.py <directorio> [Opc: <archivo_stopwords>]")
        sys.exit(1)

    directorio = sys.argv[1]
    archivo_stopwords = sys.argv[2] if len(sys.argv) > 2 else None

    analizador_lexico(directorio, archivo_stopwords)

    print("Analizador lexico CON STEMMING realizado, archivo .txt exportado.")

