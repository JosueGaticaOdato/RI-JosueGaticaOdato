import os, re, json
from collections import defaultdict

# ----------- LECTURA DE ARCHIVOS -----------------

testCollection = "../Colecciones/RE_collection_test/collection_test_ER2"

# Ruta de los documentos
base_dir = os.path.dirname(os.path.abspath(__file__))
ruta = os.path.join(base_dir, testCollection)
print(ruta)
ruta_salida = os.path.join(base_dir, "collection.json")

# Lectura de archivos
archivos = [f for f in os.listdir(ruta) if f.endswith(".txt")]

token_especificos = [
    ('EMAIL', r"[a-zA-Z0-9][a-zA-Z0-9._%+\-]*@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"),
    ('URL', r'(?:https?|ftps?)://[^\s<>"\'`]+'), 
    ('ABBREV_MULTI', r"(?:[A-Za-záéíóúüñÁÉÍÓÚÜÑ]{1,4}\.){1,}[A-Za-záéíóúüñÁÉÍÓÚÜÑ]{1,4}\.?"), # Abreviaturas S.A. o U.S.A.
    ('ABBREV', r"[A-Za-záéíóúüñÁÉÍÓÚÜÑ]{2,10}\."), # Abreviaturas Dr., Lic.
    ('PHONE', r"[+\-]?\d[\d.,\-]*(?:%|°)?"), # Telefonos
    ('NUMBER', r'\d+(?:[.,]\d+)*'),
    ('FECHA', r"\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{4}"),
    ('PROPER_NOUN', r"(?:[A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]+)(?:\s+(?!Sra\b|Sr\b|Dr\b)[A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]+)+"), # Nombres propios, con varias palabras con mayúscula
    ('WORD', r"[a-záéíóúüñA-ZÁÉÍÓÚÜÑ]{2,}"),
    ('PUNCT', r'[¡!¿?.,;:]'),
    ('SIGLA', r"[A-ZÁÉÍÓÚÜÑ]{2,}")
]

def nuevo_tokenizer(texto):
    tok_regex = '|'.join(f'(?P<{name}>{regex})' for name, regex in token_especificos)
    
    tokens = []
    
    for match in re.finditer(tok_regex, texto):
        kind = match.lastgroup
        value = match.group().strip()
        
        tokens.append(value)
    
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

    #print(os.path.join(ruta, archivo))
    with open(os.path.join(ruta, archivo), "r", encoding="utf-8") as f:
      texto = f.read()

    # Obtengo los tokens
    tokens = nuevo_tokenizer(texto)
    total_tokens += len(tokens)

    # Construccion del indice
    for token in tokens:
      indice[token][doc_id] += 1
    
    # Agregar palabras al vocabulario (como es conjunto no repite, obteniendo los terminos unicos)
    vocabulario.update(tokens)

# ----------- SALIDA EN JSON -----------------

salida = {"data": [], "statistics": {} }

for termino, docs in indice.items():
    # Ordenar documentos por docid
    pares_ordenados = sorted(docs.items())

    docids = [doc for doc, _ in pares_ordenados]
    freqs = [freq for _, freq in pares_ordenados]

    entrada = {
        "term": termino,
        "docid": docids,
        "freq": freqs,
        "df": len(docids)
    }
    print(termino)
    salida["data"].append(entrada)

salida["statistics"] = {
    "N": documentos,
    "num_terms": len(vocabulario),
    "num_tokens": total_tokens
}

print("Exportando en", ruta_salida)

with open(ruta_salida, "w", encoding="utf-8") as f:
    json.dump(salida, f, indent=2)
