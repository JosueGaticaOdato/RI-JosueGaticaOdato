"""
Implementacion BSBI
"""

import argparse
from dataclasses import dataclass, field
import os
import pickle
import re
import struct
import time
from typing import ClassVar, Tuple

# ----------- CONSTANTES GLOBALES -----------------

LEN_POSTING   =   8         # 4 bytes para docID, 4 bytes para freq (2 * 4)
LEN_NUM       =   4         # Bytes por entero (formato I, big-endian)
RECORD_SIZE   =   12        # Bytes por registro. 3 * 4 (termID, docID, freq)
FMT_RECORD    =   ">3I"     # termID, docID, freq
FMT_POSTING   =   ">2I"     # docID, freq

# ------  FUNCIONES (TOKENIZER, WRITER-CHUNK, ETC. ) -------------

def tokenizer(texto, stopwords=None, minimo=1, maximo=float("inf")):
  """
  Tokenizer que pasa todo a minuscula y se queda con letras con acento y ñ

  Args: texto, stopwords, minimo, maximo

  Returns:
      tokens
  """
  texto = texto.lower() # Minusculas

  tokens = re.findall(r"[a-záéíóúüñ]+", texto) #Solo letras con acento y ñ

  tokens_validos = []
  for token in tokens:
      
      # Stopwords
      if stopwords and token in stopwords:
          continue
      
      # Minimo y maximo
      if len(token) > maximo or len(token) < minimo:
          continue
      
      tokens_validos.append(token)

  return tokens_validos

def parse_document(path):
  """
  Dado un path, abro el archivo y aplico el tokenizer

  Args: path

  Returns: tokens
  """
  with open(path, "r", encoding="utf-8", errors="ignore") as f:
    return tokenizer(f.read())

def _tokens_from_document(documento):
  "Normaliza un documento a una lista de tokens."
  if isinstance(documento, str):
    if os.path.exists(documento):
      return parse_document(documento)
    return tokenizer(documento)
  return list(documento)

def _iter_corpus(corpus):
  "Permite recibir corpus como [(docid, doc), ...] o como [doc, ...]."
  for generated_docid, item in enumerate(corpus):
    if isinstance(item, tuple) and len(item) == 2:
      docid, documento = item
      yield docid, documento
    else:
      yield generated_docid, item

# Escritura de un chunk a disco
def write_chunk(partial_tuples, chunk_path):
  """
  Ordena las tuplas (term_id, docid, freq) y las escribe en binario.
  """
  partial_tuples.sort(key=lambda t: (t[0], t[1]))
  flat = [val for tupla in partial_tuples for val in tupla]

  with open(chunk_path, "wb") as f:
    if flat:
      f.write(struct.pack(f">{len(flat)}I", *flat))

# --------------  PostingChunk  -------------------

@dataclass
class PostingChunk:
   
  """
  Clase para manejo de Chunks (term_id, docid, freq). Es un cursor de lectura sobre un archivo binario de un chunk
  Cada registro ocupa 3 x 4 = 12 bytes en formato big-endian.
  """

  # -------------- ATRIBUTOS ----------------
  chunk_path:   str
  chunk_id:     int = 0
  term_id:      int = None
  docid:        int = None
  freq:         int = None
  seek:         int = 0

  _exhausted: bool   = field(default=False, init=False, repr=False) # Indica si ya no quedan registros por leer
  _file_pointer: object = field(init=False, repr=False) # Archivo donde se lee
  _NUM_PER_RECORD: ClassVar[int] = 3   # term_id, docid, freq
  _LEN_NUM: ClassVar[int] = LEN_NUM

  # -------------- METODOS ----------------

  def __post_init__(self):
    "Imicializar el descriptor de archivo y leer el primer registro"
    self._fp = open(self.chunk_path, "rb") # "rb" modo binario 
    self._read_record() # Me paro en el primer posting

  def _read_record(self) -> None:
    "Lee un registro basado  en seek utilizando unpack"
    raw = self._fp.read(RECORD_SIZE) # Lee 12, osea, term doc y freq

    if len(raw) < RECORD_SIZE: # Si no alcanza la cantidad llegue al final del archivo
      self.term_id = None
      self.docid = None
      self.freq = None
      self._exhausted = True
    
    else:
      self.term_id, self.docid, self.freq = struct.unpack(FMT_RECORD, raw) # Convierte a bytes 
      self.seek += RECORD_SIZE # Aumento el puntero, ya que es un contador de bytes leidos

  def next(self) -> None:
    "Mover el puntero seek al siguente registro"
    if not self._exhausted:
      self._read_record()    


  def get_record(self) -> Tuple[int, int, int]:
    "Retorna una tupla com (term_id, doc_id, freq)"
    return (self.term_id, self.docid, self.freq)

  # ----------------- Metodos adicionales -----------------------

  def close(self):
    "Cerrar el archivo"
    if self._fp:
      self._fp.close()
      self._fp = None

  def is_exhausted(self) -> bool:
    "Devuelve si el cursor ya llego al final del archivo"
    return self._exhausted

# --------------  BSBI  -------------------

# --------------  1. BSBI - INDEX  -------------------

def bsbi_index(corpus, memoryLimit, index_root_path, index_name):
  """
  BSBI - Index

  Paso 1: Parseo y volcado a chunks

  Args:
      corpus              : lista de documentos
      memoryLimit         : número de docs a procesar antes de volcar a disco
      index_root_path     : directorio donde guardar los chunks
      index_name          : nombre del archivo índice final

  Returns:
      
  """

  # INICIALIZACIÓN
  term2id        = {}     # palabra → ID numérico
  doc_map        = {}
  max_term_id    = 0      # contador de IDs únicos
  memory_counter = 0      # docs en memoria actual
  partial_tuples = []     # lista de (term_id, docid, freq)
  chunk_id       = 0      # contador de archivos chunk

  if memoryLimit <= 0:
    raise ValueError("memoryLimit debe ser mayor a 0")

  os.makedirs(index_root_path, exist_ok=True)

  # Volcado del chunk a disco
  def flush_chunk():
    nonlocal partial_tuples, memory_counter, chunk_id
    chunk_path = os.path.join(index_root_path, f"chunk{chunk_id}.bin")
    write_chunk(partial_tuples, chunk_path)
    print(f"chunk {chunk_id:04d} volcado "
      f"({memory_counter} docs, {len(partial_tuples)} tuplas)")
    chunk_id += 1
    partial_tuples = []
    memory_counter = 0

  print("\n" + "=" * 55)
  print("Comienzo del algoritmo BSBI")
  print(f"Colección: {len(corpus)} documentos - volcado cada {memoryLimit} docs")
  print("=" * 55 + "\n")

  t0 = time.perf_counter()

  # PARA CADA (docid, documento) en corpus:
  for docid, documento in _iter_corpus(corpus):
    doc_map[docid] = documento

    # Paso 1: frecuencias por termino en este documento
    term_freq_in_doc = {}
    for palabra in _tokens_from_document(documento):
      if palabra not in term2id:
        max_term_id += 1
        term2id[palabra] = max_term_id

      term_freq_in_doc[palabra] = term_freq_in_doc.get(palabra, 0) + 1

    # Paso 2: generar tuplas (term_id, docid, freq)
    for termino, freq in term_freq_in_doc.items():
      partial_tuples.append((term2id[termino], docid, freq))

    memory_counter += 1

    # Paso 3: limite de memoria alcanzado -> volcar chunk a disco
    if memory_counter >= memoryLimit:
      flush_chunk()

  # Volcado del ultimo bloque (puede quedar sin llegar al limite)
  if partial_tuples:
    flush_chunk()

  time_index = time.perf_counter() - t0
  index_path = os.path.join(index_root_path, f"{index_name}.bin")
  vocab_path = os.path.join(index_root_path, f"{index_name}_vocab.pkl")

  # Merge
  t0 = time.perf_counter()
  vocabulary = bsbi_merge(term2id, chunk_id, index_root_path, index_path, vocab_path)
  time_merge = time.perf_counter() - t0

  print("\n" + "=" * 55)
  print("  FIN del allgortimo BSBI")
  print("=" * 55)

  return {
    "term2id": term2id,
    "vocabulary": vocabulary,
    "doc_map"   : doc_map,
    "chunk_count": chunk_id,
    "index_path": index_path,
    "vocab_path": vocab_path,
    "time_index": time_index,
    "time_merge": time_merge
  }


# --------------  2. BSBI - MERGE  -------------------

def bsbi_merge(term2id, chunk_count, index_root_path, index_path, vocab_path):
  """
  Mergea los chunks generados por BSBI y crea el indice binario final con postings (docid, freq) y el vocabulario pickle: termino -> [seek, df, term_id]
  """
  id2term = {term_id: term for term, term_id in term2id.items()}
  chunks = []

  # Punteros a cada chunk
  for i in range(chunk_count):
    chunk_path = os.path.join(index_root_path, f"chunk{i}.bin")
    if os.path.exists(chunk_path) and os.path.getsize(chunk_path) > 0:
      chunks.append(PostingChunk(chunk_path=chunk_path, chunk_id=i))

  vocabulary = {}
  seek_actual = 0

  try:
    with open(index_path, "wb") as index_file:

      # Iterar sobre todos los term_ids en orden
      for term_id_actual in sorted(id2term):
        posting_list = []

        for chunk in chunks:
          while not chunk.is_exhausted() and chunk.term_id < term_id_actual:
            chunk.next()

          while not chunk.is_exhausted() and chunk.term_id == term_id_actual:
            _, docid, freq = chunk.get_record()
            posting_list.append((docid, freq))
            chunk.next()

        if posting_list:
          posting_list.sort(key=lambda posting: posting[0])
          flat = [val for posting in posting_list for val in posting]
          index_file.write(struct.pack(f">{len(flat)}I", *flat))

          term = id2term[term_id_actual]
          df = len(posting_list)
          vocabulary[term] = [seek_actual, df, term_id_actual]
          seek_actual += df * LEN_POSTING

    # Guardar vocabulario como pickle
    with open(vocab_path, "wb") as vocab_file:
      pickle.dump(vocabulary, vocab_file)

  finally:
    for chunk in chunks:
      chunk.close()

  return vocabulary

# --------------  BUILD INDEX  -------------------
 
def build_index(collection_path: str,
                n: int,
                chunks_dir: str,
                index_name: str = "index") -> None:

  """
  Construccion del indice siguiendo los siguientes pasos:
   1. Indexar por bloque y chunk
   2. Merge de chunk, teniendo indice final y vocabulario
  """
  os.makedirs(chunks_dir, exist_ok=True)

  archivos = sorted(
    archivo
    for archivo in os.listdir(collection_path)
    if archivo.endswith(".txt")
  )

  corpus = [
    (docid, os.path.join(collection_path, archivo))
    for docid, archivo in enumerate(archivos, start=1)
  ]


  # Construccion del indice con merge
  resultado = bsbi_index(
    corpus=corpus,
    memoryLimit=n,
    index_root_path=chunks_dir,
    index_name=index_name
  )

  # ----------- RESULTADOS ------------
  col_size   = sum(
    os.path.getsize(os.path.join(collection_path, f))
    for f in os.listdir(collection_path)
    if not f.startswith(".")
  )
  idx_size   = os.path.getsize(resultado["index_path"])  if os.path.exists(resultado["index_path"])  else 0
  vocab_size = os.path.getsize(resultado["vocab_path"])  if os.path.exists(resultado["vocab_path"])  else 0
  total_idx  = idx_size + vocab_size

  overhead = total_idx / col_size if col_size > 0 else 0.0

  time_index = resultado["time_index"]
  time_merge = resultado["time_merge"]
  vocabulary = resultado["vocabulary"]
  chunk_count = resultado["chunk_count"]
  doc_map = resultado["doc_map"]

  print("\n" + "=" * 55)
  print("  RESULTADOS")
  print("=" * 55)
  print(f"  Colección           : {col_size/1024:.1f} KB")
  print(f"  Índice binario      : {idx_size/1024:.1f} KB")
  print(f"  Vocabulario (pickle): {vocab_size/1024:.1f} KB")
  print(f"  Total índice        : {total_idx/1024:.1f} KB")
  print(f"  Overhead (idx/col)  : {overhead:.4f}  ({overhead*100:.1f}%)")
  print(f"  Tiempo indexación   : {time_index:.4f} s")
  print(f"  Tiempo merge        : {time_merge:.4f} s")
  print(f"  Tiempo total        : {time_index+time_merge:.4f} s")
  print(f"  Términos (vocab)    : {len(vocabulary)}")
  print(f"  Documentos          : {len(doc_map)}")
  print(f"  Chunks generados    : {chunk_count}")
  print("=" * 55)


  return resultado

# --------------  MAIN  -------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="BSBI Indexer"
    )
    parser.add_argument("collection",
                        help="Directorio con los documentos")
    parser.add_argument("-n", "--block-size", type=int, default=10,
                        help="Documentos por bloque (volcado a disco)")
    parser.add_argument("--index-dir",  default="index",
                        help="Directorio para el índice final")
    parser.add_argument("--chunks-dir", default="chunks",
                        help="Directorio para los chunks parciales")
    parser.add_argument("--index-name", default="index",
                        help="Nombre base del índice")
    args = parser.parse_args()

    build_index(
        collection_path=args.collection,
        n=args.block_size,
        chunks_dir=args.chunks_dir,
        index_name=args.index_name,
    )
