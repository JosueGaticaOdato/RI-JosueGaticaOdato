"""
Recuperacion de Skip-list dado un termino
"""

import argparse
import math
import os
import pickle
import struct


# --------------  CONSTANTES  -------------------

LEN_POSTING   =   8         # 4 bytes para docID, 4 bytes para freq (2 * 4)
FMT_POSTING   =   ">2I"     # docID, freq

# --------------  FUNCIONES  -------------------

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

# --------------- MOSTRAR SKIP -------------------

def mostrar_estructura_skip_list(skip_list, docmap):
    """
    Muestra la estructura completa de la skip list incluyendo bloques.
    """
    #print("Skip List:")
    for max_doc_id, offset in skip_list:
        doc_name = docmap.get(max_doc_id, f"Doc_{max_doc_id}")
        print(f"{doc_name}:{max_doc_id}")

# ------------------ OBTENER SKIP ---------------------

def obtener_skip_list(termino, vocab, docmap, index_path):
    """
    Recupera los punteros de la skip list para un término dado.
    
    Proceso:
    1. Lee el posting list completo del término
    2. Calcula la skip list (dividiendo en bloques de K)
    3. Retorna lista de (docName, docID) para cada máximo de bloque
    """
    if termino not in vocab:
        print(f"El término '{termino}' no se encuentra en el vocabulario.")
        return []
    
    # Leer posting list completo
    posting_list = leer_posting_list(termino, vocab, index_path)
    if not posting_list:
        return []
    
    # Calcular skip list
    return armar_skip_list(posting_list)

# -------------------- MAIN --------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Obtener Skip Lists de Termino"
    )
    parser.add_argument("term",
        help='Término a buscar')
    parser.add_argument("--index-dir",  default="TP4/EJ1/index_debug",
        help="Directorio del índice (default: TP4/EJ1/index_debug)")
    parser.add_argument("--index-name", default="index_debug",
        help="Nombre base del índice (default: index_debug)")
    
    args = parser.parse_args()

    vocabulary, doc_map = cargar_indice(args.index_dir, args.index_name)
    index_path = os.path.join(args.index_dir, f"{args.index_name}.bin")

    skip_list = obtener_skip_list(args.term, vocabulary,doc_map, index_path)
    mostrar_estructura_skip_list(skip_list, doc_map)
    

if __name__ == "__main__":
    main()