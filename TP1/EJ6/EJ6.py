import numpy as np
import os

# ---------- VARIABLES -----------

# MODIFICAR UBICACION DE LA COLECCION
coleccion = "../Colecciones/languageIdentificationData"
nombre_soluciones = "sol_ej6.txt"

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


# Calculo de frecuencia de letras dado un texto
def frecuencia_letras(texto):
    texto = texto.lower()
    letras = [letra for letra in texto if letra.isalpha()]
    total_letras = len(letras)
    frecuencia_letras = {
        letra: letras.count(letra) / total_letras for letra in set(letras)
    }
    return frecuencia_letras


# Dadas dos frecuencias, se evalua su correlacion
def correlacion(freq_texto, freq_entrenamiento):
    letras_comunes = set(freq_texto) & set(freq_entrenamiento)
    frecuencia_texto_comun = np.array([freq_texto[letra] for letra in letras_comunes])
    frecuencia_entrenamiento_comun = np.array(
        [freq_entrenamiento[letra] for letra in letras_comunes]
    )
    correlacion = np.corrcoef(frecuencia_texto_comun, frecuencia_entrenamiento_comun)[
        0, 1
    ]
    return correlacion


# Identificar idioma
def identificar_idioma(texto_prueba, conjunto_entrenamiento):
    frecuencia_texto = frecuencia_letras(texto_prueba)
    mejor_correlacion = -1
    mejor_idioma = None
    for idioma, texto_entrenamiento in conjunto_entrenamiento.items():
        frecuencia_entrenamiento = frecuencia_letras(texto_entrenamiento)
        correlacion_idioma = correlacion(frecuencia_texto, frecuencia_entrenamiento)
        if correlacion_idioma > mejor_correlacion:
            mejor_correlacion = correlacion_idioma
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
              idioma_identificado = identificar_idioma(linea, entrenamiento)
              #print(idioma_identificado)
              #print(f"{i} {idioma_identificado}")
              file.write(f"{i} {idioma_identificado}\n")
              print(f"Lineas analizadas hasta el momento: {i}/{len(lineas)}" )

def comparar_archivos(path1, path2):
    iguales = 0
    total = 0
    
    with open(path1, "r", encoding="utf-8") as f1, open(path2, "r", encoding="utf-8") as f2:
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

print("Ejecutando identificador de idiomas (Basado en distribucion de letras)...")
identificar_idioma_linea(archivo_prueba, entrenamiento)
print("Archivo con soluciones exportado!")

# ---------------- COMPARAR ACIERTOS ----------------

#Soluciones
iguales1, total1, porcentaje1 = comparar_archivos(nombre_soluciones, os.path.join(ruta, archivo_soluciones))

# Langdetect
iguales2, total2, porcentaje2 = comparar_archivos(nombre_soluciones, archivo_langdetect)


with open("resultados-metodo1.txt", "w", encoding="utf-8") as resultados_file:
    resultados_file.write(
        f"Resultados - Distribucion de la frecuencia de las letras\n"
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
