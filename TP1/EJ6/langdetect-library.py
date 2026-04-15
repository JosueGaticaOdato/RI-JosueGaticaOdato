import os
from langdetect import detect

# ---------- VARIABLES -----------

# MODIFICAR UBICACION DE LA COLECCION
coleccion = "../Colecciones/languageIdentificationData"
nombre_soluciones = "langdetect.txt"

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

def identificar_idioma_linea(prueba):
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
              idioma_identificado = detect(linea)
              idioma = "French"
              if idioma_identificado == "it":
                idioma = "Italian"
              elif idioma_identificado == "en":
                idioma = "English"
              elif idioma_identificado == "es":
                idioma = "Español"
              #print(idioma_identificado)
              #print(f"{i} {idioma_identificado}")
              file.write(f"{i} {idioma}\n")
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

archivo_prueba = "test"
archivo_langdetect = "langdetect"
archivo_soluciones = "solution"

print("Ejecutando identificador de idiomas LangDetect...")
identificar_idioma_linea(archivo_prueba)
print("Archivo con soluciones exportado!")

# ---------------- COMPARAR ACIERTOS ----------------

#Soluciones
iguales1, total1, porcentaje1 = comparar_archivos(nombre_soluciones, os.path.join(ruta, archivo_soluciones))

with open("resultados-langdetect.txt", "w", encoding="utf-8") as resultados_file:
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