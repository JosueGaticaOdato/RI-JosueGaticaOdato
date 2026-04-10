import numpy as np
import os

# ---------- VARIABLES -----------

# MODIFICAR UBICACION DE LA COLECCION
coleccion = "../Colecciones/languageIdentificationData"
nombre_soluciones = "sol_ej6matriz.txt"

base_dir = os.path.dirname(os.path.abspath(__file__))
ruta = os.path.join(base_dir, coleccion)

# --------- FUNCIONES -----------


# Carga del conjunto de entrenamiento
def cargar_entrenamiento(rutas):
    conjunto_entrenamiento = {}

    for idioma, ruta_relativa in rutas.items():
        mi_ruta = os.path.join(ruta, ruta_relativa)

        with open(mi_ruta, "r", encoding="latin1") as archivo:
            texto_entrenamiento = archivo.read()
            conjunto_entrenamiento[idioma] = texto_entrenamiento
    return conjunto_entrenamiento


# Función para calcular la matriz de probabilidades de letras consecutivas
def calcular_probabilidades_consecutivas(texto):
    texto = texto.lower()
    letras = [letra for letra in texto if letra.isalpha()]
    alfabeto = sorted(set(letras))
    num_letras = len(alfabeto)
    matriz_probabilidades = np.zeros((num_letras, num_letras))
    letra_anterior = None
    for letra in letras:
        if letra_anterior is not None:
            indice_anterior = alfabeto.index(letra_anterior)
            indice_actual = alfabeto.index(letra)
            matriz_probabilidades[indice_anterior][indice_actual] += 1
        letra_anterior = letra
    # Normalizar las probabilidades
    matriz_probabilidades /= matriz_probabilidades.sum(axis=1, keepdims=True)
    return matriz_probabilidades, alfabeto


# Función para calcular la probabilidad de una cadena dada una matriz de probabilidades de transición
def calcular_probabilidad_cadena(cadena, matriz_probabilidades, alfabeto):
    probabilidad = 1.0
    for i in range(len(cadena) - 1):
        letra_actual = cadena[i]
        letra_siguiente = cadena[i + 1]
        if (
            letra_actual in alfabeto and letra_siguiente in alfabeto
        ):  # Verificar si ambas letras están en el alfabeto
            indice_actual = alfabeto.index(letra_actual)
            indice_siguiente = alfabeto.index(letra_siguiente)
            probabilidad_transicion = matriz_probabilidades[indice_actual][
                indice_siguiente
            ]
            probabilidad *= probabilidad_transicion
    return probabilidad

# Función para identificar el idioma basado en la probabilidad de transición de letras
def identificar_idioma_probabilidades_transicion(texto_prueba, conj_entrenamiento):
    probabilidades_entrenamiento = {}
    for idioma, texto_entrenamiento in conj_entrenamiento.items():
        matriz_probabilidades, alfabeto = calcular_probabilidades_consecutivas(
            texto_entrenamiento
        )
        probabilidades_entrenamiento[idioma] = matriz_probabilidades, alfabeto

    mejor_idioma = None
    mejor_probabilidad = 0
    for idioma, (
        matriz_probabilidades,
        alfabeto,
    ) in probabilidades_entrenamiento.items():
        probabilidad = calcular_probabilidad_cadena(
            texto_prueba, matriz_probabilidades, alfabeto
        )
        if probabilidad > mejor_probabilidad:
            mejor_probabilidad = probabilidad
            mejor_idioma = idioma
    return mejor_idioma

def identificar_idioma_linea(prueba, entrenamiento):
    with open(os.path.join(ruta, prueba), "r", encoding="latin1") as archivo:
        texto_prueba = archivo.read()

    lineas = texto_prueba.split("\n")
    i = 0
    with open(nombre_soluciones, "w", encoding="utf-8") as file:
        for linea in lineas:
            i += 1
            linea = (
                linea.strip()
            )  # Eliminar espacios en blanco al inicio y al final de la línea
            if linea:  # Saltar líneas en blanco
                idioma_identificado = identificar_idioma_probabilidades_transicion(linea, entrenamiento)
                file.write(f"{i} {idioma_identificado}\n")
                print(f"Lineas analizadas hasta el momento: {i}/{len(lineas)}")

def comparar_archivos(path1, path2):
    iguales = 0
    total = 0

    with open(path1, "r", encoding="utf-8") as f1, open(path2, "r", encoding="utf-8"
    ) as f2:
        for linea1, linea2 in zip(f1, f2):
            total += 1

            if linea1.strip().lower() == linea2.strip().lower():
                iguales += 1

    porcentaje = (iguales / total) * 100 if total > 0 else 0

    return iguales, total, porcentaje


# ----------------- MAIN -----------------------

archivos_entrenamiento = {
    "English": "training/English",
    "French": "training/French",
    "Italian": "training/Italian",
}

archivo_prueba = "test"
archivo_soluciones = "solution"
archivo_langdetect = "langdetect.txt"

entrenamiento = cargar_entrenamiento(archivos_entrenamiento)

print("Ejecutando identificador de idiomas (Basado en Probabilidad)...")
identificar_idioma_linea(archivo_prueba, entrenamiento)
print("Archivo con soluciones exportado!")

# ---------------- COMPARAR ACIERTOS ----------------

#Soluciones
iguales1, total1, porcentaje1 = comparar_archivos(nombre_soluciones, os.path.join(ruta, archivo_soluciones))

# Langdetect
iguales2, total2, porcentaje2 = comparar_archivos(nombre_soluciones, archivo_langdetect)

with open("resultados-metodo2.txt", "w", encoding="utf-8") as resultados_file:
    resultados_file.write(
        f"Resultados - Probabilidad de letras precedentes\n"
    )
    resultados_file.write(
        f"---- COMPARACION CON LA SOLUCION PROVISTA -------\n"
    )
    resultados_file.write(
        f"Líneas iguales: {iguales1}\n"
    )
    resultados_file.write(
        f"Total líneas: {total1}\n"
    )
    resultados_file.write(
        f"Porcentaje: {porcentaje1:.2f}%\n"
    )
    resultados_file.write(
        f"---- COMPARACION CON LANGDETECT -------\n"
    )
    resultados_file.write(
        f"Líneas iguales: {iguales2}\n"
    )
    resultados_file.write(
        f"Total líneas: {total2}\n"
    )
    resultados_file.write(
        f"Porcentaje: {porcentaje2:.2f}%\n"
    )
