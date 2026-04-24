import os, re, math
from collections import Counter
from bs4 import BeautifulSoup


# ----------- LECTURA DE ARCHIVOS -----------------

# ---- Procesamiento de WIKI-SMALL con BeautifulSoup -----

def extract_text_from_html(filepath:str):
  with open(filepath, "r", encoding="utf-8") as file:
    soup = BeautifulSoup(file,"html.parser")
    return soup.get_text(separator=" ", strip= True)

def process_wiki_collection(root_dir: str) -> dict:
    documents = {}
    html_files = []

    # 1. Escanear rápido solo para saber la cantidad total
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith(".html"):
                html_files.append(os.path.join(dirpath, filename))

    total_docs = len(html_files)
    print(f"Se encontraron {total_docs} documentos HTML.\n")

    # 2. Tu proceso original intacto, sumando el contador
    for index, full_path in enumerate(html_files, start=1):
        relative_path = os.path.relpath(full_path, root_dir)
        
        try:
            # Tu lógica original exacta
            text = extract_text_from_html(full_path)
            documents[relative_path] = text
        except Exception as e:
            # El \n es solo para que el error no se imprima arriba del contador
            print(f"\nError leyendo {full_path}: {e}")
        
        # El print del contador
        faltantes = total_docs - index
        print(f"\rProcesando: {index}/{total_docs} | Faltan: {faltantes}", end="", flush=True)

    print("\n\n¡Procesamiento completado!")
    return documents

# ---------- TOKENIZER -------------------------

def tokenizer(texto):
   return re.findall(r"[a-z]+", texto.lower()) 

# ----------- NUEVO TOKENIZER --------------------

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

def nuevo_tokenizer(texto,stopwords = None, minimo = 2, maximo =float('inf')):
    tok_regex = '|'.join(f'(?P<{name}>{regex})' for name, regex in token_especificos)
    
    tokens = []
    
    for match in re.finditer(tok_regex, texto):
        kind = match.lastgroup
        value = match.group().strip()

        # Stopwords
        if stopwords and value in stopwords:
            continue
        
        # Minimo y maximo
        if len(value) > maximo or len(value) < minimo:
            continue
        
        tokens.append(value)
    
    return tokens

# ----------- FUNCIONALIDADES -----------------

def print_vocabulario(vocabulario):
    print("\n===== VOCABULARIO =====\n")
    
    for term, data in vocabulario.items():
        if data["df"] != 1:   
          print(f"Término: '{term}'")
          print(f"  DF: {data['df']}")
          print(f"  Postings:")
          
          for doc_id, weight in data["postings"]:
            print(f"    -> Doc: {doc_id} | Peso TF-IDF: {weight:.4f}")
          
          print("-" * 40)

def print_vocabulario_compacto(vocabulario):
    print("\n===== VOCABULARIO (RESUMEN) =====\n")
    
    for term, data in vocabulario.items():
        docs = [doc_id for doc_id, _ in data["postings"]]
        print(f"{term:15} | DF={data['df']:3} | Docs={docs}")

def read_stopwords(archivo_stopwords):
    with open(archivo_stopwords, "r", encoding="utf-8") as file:
      stopwords = set(file.read().splitlines())
    return stopwords

def calcular_tf(tokens):
    return Counter(tokens)

def construir_indice(docs, stopwords=None):
    vocabulario = {}
    N = len(docs)

    # guardar TF por documento
    tf_docs = {}

    print(f"\n[Fase 1/2] Calculando TF y armando vocabulario ({N} documentos)...")
    
    # Envolvemos docs.items() en un enumerate para tener el contador
    for index, (doc_id, data) in enumerate(docs.items(), start=1):
        
        tokens = nuevo_tokenizer(data, stopwords)
        tf = calcular_tf(tokens)
        tf_docs[doc_id] = tf

        for term in tf:
            if term not in vocabulario:
                vocabulario[term] = {"df": 0, "postings": []}
            vocabulario[term]["df"] += 1

        # Contador Fase 1
        faltantes = N - index
        print(f"\rProcesando doc: {index}/{N} | Faltan: {faltantes}", end="", flush=True)

    
    total_terminos = len(vocabulario)
    print(f"\n\n[Fase 2/2] Calculando TF-IDF para {total_terminos} términos...")
    
    # calcular TF-IDF
    # Envolvemos vocabulario.items() en un enumerate
    for index, (term, data) in enumerate(vocabulario.items(), start=1):
        

        df = data["df"]
        idf = math.log(N / df)

        for doc_id, tf in tf_docs.items():
            if term in tf:
                freq = tf[term]
                weight = (1 + math.log(freq)) * idf
                data["postings"].append((doc_id, weight))
        
        # Contador Fase 2
        faltantes_term = total_terminos - index
        print(f"\rProcesando término: {index}/{total_terminos} | Faltan: {faltantes_term}", end="", flush=True)

    print("\n\n¡Índice construido con éxito!")
    return vocabulario

def calcular_normas(vocabulario):
    norms = {}
    total_terminos = len(vocabulario)

    print(f"\n[Fase 1/2] Sumando pesos al cuadrado para {total_terminos} términos...")
    
    # Fase 1: Envolvemos vocabulario.items() con enumerate
    for index, (term, data) in enumerate(vocabulario.items(), start=1):
        

        for doc_id, weight in data["postings"]:
            norms[doc_id] = norms.get(doc_id, 0) + weight**2
        
        # Contador Fase 1
        faltantes = total_terminos - index
        print(f"\rProcesando término: {index}/{total_terminos} | Faltan: {faltantes}", end="", flush=True)

    
    total_docs = len(norms)
    print(f"\n\n[Fase 2/2] Aplicando raíz cuadrada a {total_docs} documentos...")

    # Fase 2: Envolvemos la iteración del diccionario norms con enumerate
    # Usamos list(norms.keys()) para poder iterarlo limpiamente con el índice
    for index, doc_id in enumerate(list(norms.keys()), start=1):
        
        norms[doc_id] = math.sqrt(norms[doc_id])
        
        # Contador Fase 2
        faltantes_docs = total_docs - index
        print(f"\rProcesando doc: {index}/{total_docs} | Faltan: {faltantes_docs}", end="", flush=True)

    print("\n\n¡Cálculo de normas completado!")
    return norms

# ----------- PROCESAMIENTO CONSULTAS -----------------

def vector_query(query, vocabulario, N):
    tokens = nuevo_tokenizer(query)
    tf = calcular_tf(tokens)

    #print(tokens)
    q_vec = {}

    for term, freq in tf.items():
        if term in vocabulario:
            df = vocabulario[term]["df"]
            idf = math.log(N / df)
            q_vec[term] = (1 + math.log(freq)) * idf

    return q_vec

def rankear(query, vocabulario, norms, N):
    q_vec = vector_query(query, vocabulario, N)
    scores = {}

    for term, q_weight in q_vec.items():
        if term in vocabulario:
            for doc_id, d_weight in vocabulario[term]["postings"]:
                scores[doc_id] = scores.get(doc_id, 0) + q_weight * d_weight

    # normalizar (coseno)
    for doc_id in scores:
        scores[doc_id] /= norms[doc_id]

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)

# ----------- MAIN -----------------

root_directory = "../Colecciones/test/"
#root_directory = "../Colecciones/en/articles/"
docs_wiki = process_wiki_collection(root_directory)

archivo_stopwords = "stopwords.txt"
stopwords = read_stopwords(archivo_stopwords)

#Muestra primeras 50 caracteres
# for path, content in list(docs_wiki.items())[:3]:
#   print(f"{path} ->")
#   print(content[:50], "...") #

vocabulario = construir_indice(docs_wiki, stopwords)
norms = calcular_normas(vocabulario)
print_vocabulario(vocabulario)

corte = False

while not corte:
    print("1. Escribir consulta")
    print("2. Salir")
    opc = int(input("Escriba una opcion: "))
    if opc == 1:
      query = input("Consulta: ")
      ranking = rankear(query, vocabulario, norms, len(docs_wiki))
      #print(ranking)

      for doc, score in ranking[:10]:
          print(doc, score)
    elif opc == 2:
      corte = True