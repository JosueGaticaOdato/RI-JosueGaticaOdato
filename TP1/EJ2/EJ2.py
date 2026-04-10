from collections import defaultdict
import sys, os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from funciones import procesar_tokens, procesar_documento, remover_stopwords


def analizador_lexico(
    directorio, archivo_stopwords=None, minimo=1, maximo=float("inf")
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
    documento_masCorto = float("inf")
    documento_masLargo = 0

    # Largo promedio de un termino
    letras_totales_terminos = 0

    # --------- LECTURA DE ARCHIVOS ---------------

    for archivo in os.listdir(directorio):
        if archivo.endswith(".txt"):
            path = os.path.join(directorio, archivo)

            # --------- ANALISIS LEXICO ---------------

            tokens = procesar_tokens(path)
            contador_token += len(tokens)
            terminos = procesar_documento(path)

            # Eliminamos palabras vacias si existen
            if archivo_stopwords:
                terminos = remover_stopwords(terminos, archivo_stopwords)

            contador_termino += len(set(terminos))
            documento_masCorto = min(documento_masCorto, len(terminos))
            documento_masLargo = max(documento_masLargo, len(terminos))

            # Eliminamos palabras vacias si existen
            if archivo_stopwords:
                terminos = remover_stopwords(terminos, archivo_stopwords)

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
        estadisticas_file.write(
            f"Cantidad de documentos procesados: {len(os.listdir(directorio))}\n"
        )
        estadisticas_file.write(f"Cantidad de tokens extraidos: {contador_token}\n")
        estadisticas_file.write(
            f"Cantidad de terminos extraidos: {len(terminos_ordenados)}\n"
        )
        estadisticas_file.write(
            f"Promedio de tokens por documento: {promedio_token_documento}\n"
        )
        estadisticas_file.write(
            f"Promedio de terminos por documento: {promedio_termino_documento}\n"
        )
        estadisticas_file.write(
            f"Largo promedio de un termino: {letras_totales_terminos/len(terminos_ordenados)}\n"
        )
        estadisticas_file.write(
            f"Cantidad de tokens del documento mas corto: {documento_masCorto}\n"
        )
        estadisticas_file.write(
            f"Cantidad de tokens del documento mas largo: {documento_masLargo}\n"
        )
        estadisticas_file.write(
            f"Cantidad de terminos que aparecen solo 1 vez: {terminos_unavez}\n"
        )

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

    analizador_lexico(directorio, archivo_stopwords)

    print("Analizador lexico realizado, archivos .txt exportados.")
