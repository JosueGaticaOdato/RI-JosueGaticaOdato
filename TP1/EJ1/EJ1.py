import os, re, json
from collections import defaultdict

# ----------- LECTURA DE ARCHIVOS -----------------

testCollection = "../Colecciones/TestCollection"

# Ruta de los documentos
base_dir = os.path.dirname(os.path.abspath(__file__))
ruta = os.path.join(base_dir, testCollection)
print(ruta)
ruta_salida = os.path.join(base_dir, "collection.json")

# Lectura de archivos
archivos = [f for f in os.listdir(ruta) if f.endswith(".txt")]

# ----------- FUNCIONALIDADES -----------------

def normalizar(texto):
    texto = texto.lower()  # Minusculas
    texto = re.sub(r'[^a-záéíóúñ\s]', ' ', texto)  # Eliminar simbolos
    tokens = texto.split()  # Split por espacio
    return tokens

# ----------- DEFINICION DE VARIABLES -----------------

documentos = 0
total_tokens = 0
vocabulario = set()
indice = defaultdict(lambda: defaultdict(int))


# ----------- ANALISES LEXICO-----------------

print("Comenzando Analisis Lexico")

for archivo in archivos:
    documentos += 1

    # Nombre del archivo a numero
    doc_id = int(archivo.replace("doc", "").replace(".txt", ""))

    print(os.path.join(ruta, archivo))
    with open(os.path.join(ruta, archivo), "r", encoding="utf-8") as f:
      texto = f.read()

    # Obtengo los tokens
    tokens = normalizar(texto)
    total_tokens += len(tokens)

    # Construccion del indice
    for token in tokens:
      indice[token][doc_id] += 1
    
    # Agregar palabras al vocabulario (como es conjunto no repite, obteniendo los terminos unicos)
    vocabulario.update(tokens)

""" 

Ejemplo de manejo de indice invertido

tokens = ["gato", "gato", "loro"]
doc_id = 0

indice = {
    "gato": {0: 2}, Token gato, en documento 0, aparece 2 veces
    "loro": {0: 1}  Token loro, en documento 0, aparece 1 vez
}

"""

print("Fin Analisis Lexico")

# ----------- SALIDA EN JSON -----------------

salida = {"data": [], "statistics": {} }

for termino, docs in indice.items():
    # Ordenar documentos por docid
    pares_ordenados = sorted(docs.items())

    docids = [doc for doc, _ in pares_ordenados]
    freqs = [freq for _, freq in pares_ordenados]

    """
    Ejemplo: 
    De [(1,3), (5,2)] a
    
    docids = [1, 5]
    freqs = [3, 2]
    """

    entrada = {
        "term": termino,
        "docid": docids,
        "freq": freqs,
        "df": len(docids)
    }

    salida["data"].append(entrada)

salida["statistics"] = {
    "N": documentos,
    "num_terms": len(vocabulario),
    "num_tokens": total_tokens
}

print("Exportando en", ruta_salida)

with open(ruta_salida, "w", encoding="utf-8") as f:
    json.dump(salida, f, indent=2)

