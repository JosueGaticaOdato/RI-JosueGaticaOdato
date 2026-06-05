"""
Skip list al indice del ejercicio 1
"""

import argparse
import math
import os
import pickle
import struct
import time

# --------------  CONSTANTES  -------------------

LEN_POSTING   =   8         # 4 bytes para docID, 4 bytes para freq (2 * 4)
FMT_POSTING   =   ">2I"     # docID, freq

# --------------  FUNCIONES  -------------------

def cargar_indice(index_dir, index_name):
  "Cargar vocabulario y doc_map desde disco"
  vocab_path = os.path.join(index_dir, f"{index_name}_vocab.pkl")
  docmap_path = os.path.join(index_dir, f"{index_name}_docmap.pkl")
  for path, label in [(vocab_path, "vocabulario"), (docmap_path, "doc_map")]:
      if not os.path.exists(path):
          raise FileNotFoundError(f"No se encontró {label} en '{path}'. ")
  with open(vocab_path, "rb") as f:
      vocabulary = pickle.load(f)
  with open(docmap_path, "rb") as f:
      doc_map = pickle.load(f)
  return vocabulary, doc_map

def leer_posting_list(termino, vocab, index_path):
  """
  Lee el posting list completo de un término desde el índice binario.
  Retorna lista de (docid, freq) ordenada por docid.
  """
  if termino not in vocab:
      return []
  
  df, offset = vocab[termino]
  posting_list = []
  
  with open(index_path, "rb") as f:
      f.seek(offset)
      for _ in range(df):
          data = f.read(LEN_POSTING)
          if len(data) < LEN_POSTING:
              break
          doc_id, freq = struct.unpack(FMT_POSTING, data)
          posting_list.append((doc_id, freq))
  
  return posting_list

# ------------------ ARMAR SKIP ---------------------
def armar_skip_list(posting_list):
    """
    Calcula la skip list para un posting list.
    Primero divido posting_list en bloques de tamaño K, luego para cada bloque: (maxDocID, offset)
    
    Args:
        posting_list: lista de (docid, freq) ordenada
    
    Returns:
        lista de (maxDocID, offset) para cada bloque
    """
    if not posting_list:
        return []
    
    skip_list = []

    k = int(math.sqrt(len(posting_list)))
    #print(f"Valor de K: {k}")
    
    for block_start in range(0, len(posting_list), k):
        block_end = min(block_start + k, len(posting_list))
        max_doc_id = posting_list[block_end - 1][0]  # docid de la última entrada del bloque
        skip_list.append((max_doc_id, block_start))  # offset
    
    return skip_list

# ------------------ MOSTRAR SKIP ---------------------

def mostrar_estructura_skip_list(skip_list, docmap):
    """
    Muestra la estructura completa de la skip list incluyendo bloques.
    """
    print("Skip List:")
    for max_doc_id, offset in skip_list:
        print(f"({max_doc_id}, {offset})")

# ----------------- EVALUAR CONSULTA ------------------

def evaluar_consulta(posting_corta, skip, posting_larga):
    """
    Realiza AND de dos posting lists usando skip list para acelerar búsqueda en posting_larga.
    
    Algoritmo:
    1. Para cada docID en posting_corta:
       - Usar skip list para saltar bloques en posting_larga
       - Si max_docID < target_docID, pasar al siguiente bloque
       - Si max_docID >= target_docID, hacer búsqueda secuencial
    2. Si el docID está en posting_larga, agregarlo al resultado
    
    Args:
        posting_corta: lista de (docid, freq) más corta (iteramos sobre esta)
        skip: skip list de posting_larga, lista de (maxDocID, block_start_offset)
        posting_larga: lista de (docid, freq) más larga (donde buscamos)
    
    Returns:
        dict con:
            - resultado: lista de docids en la intersección
            - comparaciones_skip: número de comparaciones contra skip list
            - comparaciones_secuencial: número de comparaciones secuenciales
    """
    resultado = []
    comparaciones_skip = 0
    comparaciones_secuencial = 0
    
    # Extraer solo docIDs
    docids_larga = [doc_id for doc_id, freq in posting_larga]
    docids_corta = [doc_id for doc_id, freq in posting_corta]
    
    for target_docid in docids_corta:
        # Usar skip list para encontrar el bloque donde podría estar target_docid
        block_start = 0
        block_end = len(docids_larga)
        
        # Iterar sobre skip list para saltar bloques
        for i, (max_doc_id, block_offset) in enumerate(skip):
            comparaciones_skip += 1
            
            if max_doc_id < target_docid:
                # max_docID < target, el docID está en un bloque posterior
                block_start = block_offset
                # Calcular el fin del bloque (donde comienza el siguiente)
                if i + 1 < len(skip):
                    block_end = skip[i + 1][1]
                else:
                    # Último bloque de la skip list
                    block_end = len(docids_larga)
            else:
                # max_docID >= target, el docID podría estar en este bloque
                block_start = block_offset
                # Calcular el fin del bloque (donde comienza el siguiente)
                if i + 1 < len(skip):
                    block_end = skip[i + 1][1]
                else:
                    # Último bloque de la skip list
                    block_end = len(docids_larga)
                break
        
        # Búsqueda secuencial en el bloque encontrado
        encontrado = False
        for j in range(block_start, block_end):
            comparaciones_secuencial += 1
            if docids_larga[j] == target_docid:
                resultado.append(target_docid)
                encontrado = True
                break
            elif docids_larga[j] > target_docid:
                # Ya pasamos el docID, no está en la lista
                break
    
    return {
        "resultado": resultado,
        "comparaciones_skip": comparaciones_skip,
        "comparaciones_secuencial": comparaciones_secuencial,
        "total_comparaciones": comparaciones_skip + comparaciones_secuencial
    }


def evaluar_consulta_and(termino1, termino2, vocab, index_path, docmap):
    """
    Realiza AND de dos términos usando skip lists.
    Automatiza el proceso: lee postings, determina cuál es más corto,
    calcula skip list y ejecuta la búsqueda.
    
    Args:
        termino1, termino2: términos a buscar
        vocab: vocabulario del índice
        index_path: ruta al archivo binario del índice
        docmap: mapeo de docid a nombre
    
    Returns:
        dict con resultados y estadísticas
    """
    start = time.perf_counter()
    
    # Leer posting lists
    posting1 = leer_posting_list(termino1, vocab, index_path)
    posting2 = leer_posting_list(termino2, vocab, index_path)
    # posting1 = [(7,1), (18,1), (31,1), (52,1), (60,1), (83,1), (104,1), (135,1)]
    # posting2 = [(3,1), (5,1), (7,1), (12,1), (18,1), (20,1), (25,1), (31,1),
    #           (37,1), (45,1), (50,1), (52,1), (55,1), (60,1), (68,1), (75,1),
    #           (83,1), (90,1), (104,1), (110,1), (120,1), (135,1), (150,1), (180,1)]

    
    if not posting1 or not posting2:
        print(f"Error: uno de los términos no tiene postings")
        return None
    
    # Determinar cuál es más corto
    if len(posting1) <= len(posting2):
        posting_corta = posting1
        posting_larga = posting2
        termino_corto = termino1
        termino_largo = termino2
    else:
        posting_corta = posting2
        posting_larga = posting1
        termino_corto = termino2
        termino_largo = termino1
    
    # Calcular skip list de posting_larga
    skip = armar_skip_list(posting_larga)
    
    # Extraer docIDs
    docids_corta = [doc_id for doc_id, freq in posting_corta]
    docids_larga = [doc_id for doc_id, freq in posting_larga]
    
    print(f"\n{'='*60}")
    print(f"Consulta AND: {termino1} AND {termino2}")
    print(f"{'='*60}")
    print(f"\nTérmino '{termino_corto}' (corto): {len(docids_corta)} docs")
    #print(f"  DocIDs: {docids_corta}")
    print(f"Término '{termino_largo}' (largo): {len(docids_larga)} docs")
    #print(f"  DocIDs: {docids_larga}")
    print(f"\nSkip List de '{termino_largo}':")
    print(skip)
    #mostrar_estructura_skip_list(skip, docmap)
    
    # Ejecutar evaluación
    print(f"\n{'-'*60}")
    print(f"Búsqueda usando Skip List:")
    print(f"{'-'*60}")
    
    resultado_dict = evaluar_consulta(posting_corta, skip, posting_larga)
    
    end = time.perf_counter() - start
    
    print(f"\nComparaciones skip list: {resultado_dict['comparaciones_skip']}")
    print(f"Comparaciones secuencial: {resultado_dict['comparaciones_secuencial']}")
    print(f"Total comparaciones: {resultado_dict['total_comparaciones']}")
    print(f"Tiempo: {end}s")
    
    print(f"\n{'='*60}")
    print(f"Resultado de {termino1} AND {termino2}:")
    print(f"{'='*60}")
    print(f"DocIDs encontrados: {resultado_dict['resultado']}")
    
    # Mostrar nombres
    print(f"\nDocumentos (cantidad: {len(resultado_dict["resultado"])}):")
    for doc_id in resultado_dict['resultado']:
        doc_name = docmap.get(doc_id, f"Doc_{doc_id}")
        print(f"  {doc_name}:{doc_id}")
    
    return resultado_dict

# -------------------- MAIN --------------------------

def main():
    parser = argparse.ArgumentParser(
        description="AND usando Skip Lists"
    )
    parser.add_argument("termino1",
        help='Primer término')
    parser.add_argument("termino2",
        help='Segundo término')
    parser.add_argument("--index-dir",  default="TP4/EJ1/index_debug",
        help="Directorio del índice (default: TP4/EJ1/index_debug)")
    parser.add_argument("--index-name", default="index_debug",
        help="Nombre base del índice (default: index_debug)")
    
    args = parser.parse_args()

    try:
        vocabulary, doc_map = cargar_indice(args.index_dir, args.index_name)
        index_path = os.path.join(args.index_dir, f"{args.index_name}.bin")
        
        termino1 = args.termino1
        termino2 = args.termino2
        
        # Ejecutar consulta AND
        evaluar_consulta_and(termino1, termino2, vocabulary, index_path, doc_map)
        
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()