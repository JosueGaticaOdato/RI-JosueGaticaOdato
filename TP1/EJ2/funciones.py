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











def analizador_lexico(directorio, archivo_stopwords=None, min_length=1, max_length=float('inf')):
    term_frequency = defaultdict(int)  # Frecuencia de términos
    document_frequency = defaultdict(int)  # Document Frequency
    token_count = 0  # Variables para estadisticas.txt
    term_count = 0
    term_frequency_one = 0
    shortest_document = float("inf")
    longest_document = 0
    total_letters_terms = 0

    for filename in os.listdir(directorio):
        if filename.endswith(".txt"):
            file_path = os.path.join(directorio, filename)
            tokens = procesar_tokens(file_path)
            token_count += len(tokens)
            terms = procesar_documento(file_path)
            term_count += len(set(terms))
            shortest_document = min(shortest_document, len(terms))
            longest_document = max(longest_document, len(terms))

            if archivo_stopwords:
                terms = remover_stopwords(terms, archivo_stopwords)

            for term in terms:
                if min_length <= len(term) <= max_length:
                    term_frequency[term] += 1

            for term in set(terms):
                if min_length <= len(term) <= max_length:
                    document_frequency[term] += 1

    sorted_terms = sorted(term_frequency.items(), key=lambda x: x[1], reverse=True)
    for term, freq in term_frequency.items():
        if freq == 1:
            term_frequency_one += 1

    # Calcular estadísticas
    avg_token_per_document = token_count / len(os.listdir(directorio))
    avg_term_per_document = term_count / len(os.listdir(directorio))

    # Escribir resultados en el archivo terminos.txt
    with open("terminos.txt", "w", encoding="utf-8") as output_file:
        for term, cf in sorted_terms:
            total_letters_terms += len(term)
            output_file.write(f"{term} {cf} {document_frequency[term]}\n")

    # Escribir resultados en el archivo estadisticas.txt
    with open("estadisticas.txt", "w", encoding="utf-8") as stats_file:
        stats_file.write(
            f"Cantidad de documentos procesados: {len(os.listdir(directorio))}\n"
        )
        stats_file.write(f"Cantidad de tokens extraídos: {token_count}\n")
        stats_file.write(f"Cantidad de términos extraídos: {len(sorted_terms)}\n")
        stats_file.write(
            f"Promedio de tokens por documento: {avg_token_per_document}\n"
        )
        stats_file.write(
            f"Promedio de términos por documento: {avg_term_per_document}\n"
        )
        stats_file.write(
            f"Largo promedio de un término: {total_letters_terms/len(sorted_terms)}\n"
        )
        stats_file.write(
            f"Cantidad de tokens del documento más corto: {shortest_document}\n"
        )
        stats_file.write(
            f"Cantidad de tokens del documento más largo: {longest_document}\n"
        )
        stats_file.write(
            f"Cantidad de términos que aparecen solo 1 vez: {term_frequency_one}\n"
        )

    # Escribir resultados en el archivo frecuencias.txt
    with open("frecuencias.txt", "w", encoding="utf-8") as freq_file:
        freq_file.write(
            "Los 10 términos más frecuentes y su CF (Collection Frequency):\n"
        )
        for term, freq in sorted_terms[:10]:
            freq_file.write(f"{term} {freq}\n")

        freq_file.write(
            "\nLos 10 términos menos frecuentes y su CF (Collection Frequency):\n"
        )
        for term, freq in sorted_terms[-10:]:
            freq_file.write(f"{term} {freq}\n")
