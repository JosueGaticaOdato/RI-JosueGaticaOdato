"""
Funcion para cargar el vocabulario en memoria y recuperar posting de un termino
"""

import argparse
import os
import pickle
import struct
from BSBI import LEN_POSTING, build_index

# --------------  FUNCIONES  -------------------

def cargar_vocabulario(path):
    "Carga el vocabulario desde disco (pickle) a memoria principal"
    with open(path, "rb") as f:
        return pickle.load(f)


def cargar_doc_map(path):
    "Cargar docid map"
    with open(path, "rb") as f:
        return pickle.load(f)


def recuperar_posting(term, vocabulario, doc_map, index_path):
    """
    Recupera la posting list completa de un término.

    Proceso:
      1. vocabulary[term] → [seek, df, term_id]   O(1)
      2. file.seek(seek)
      3. Leer df × LEN_POSTING bytes
      4. struct.unpack → tupla de enteros
      5. Separar docids (::2) y freqs (1::2)

    Retorna lista de (doc_name, docid, freq) o None si el término
    no está en el vocabulario.
    """
    if term not in vocabulario:
        return None

    df, seek = vocabulario[term]

    with open(index_path, "rb") as f:
        f.seek(seek)
        raw = f.read(df * LEN_POSTING)

    n_ints = df * 2
    unpacked = struct.unpack(f">{n_ints}I", raw)

    docids = unpacked[0::2]  # índices par docids
    freqs = unpacked[1::2]  # índices impar frecuencias

    result = []
    for docid, freq in zip(docids, freqs):
        doc_name = doc_map.get(docid, f"__doc_{docid}__")
        result.append((doc_name, docid, freq))

    return result


def mostrar_posting(term, posting):
    """
    Muestra la posting list en el formato:
        DocName:docID:Frecuencia
    """
    print(f"\nPosting list del término '{term}' (df={len(posting)}):")
    print("-" * 50)
    for doc_name, docid, freq in posting:
        print(f"{doc_name}:{docid}:{freq}")
    print("-" * 50)


# --------------  MAIN  -------------------

def main():
    parser = argparse.ArgumentParser(
        description="Recupera la posting list de un termino del índice BSBI"
    )
    parser.add_argument("term", help="Termino a buscar (se normaliza a minusculas)")
    parser.add_argument(
        "--index-dir", default="index", help="Directorio donde está el indice"
    )
    parser.add_argument("--index-name", default="index", help="Nombre base del índice")
    args = parser.parse_args()

    index_dir = args.index_dir
    index_name = args.index_name
    term = args.term.lower().strip()

    index_path = os.path.join(index_dir, f"{index_name}.bin")
    vocab_path = os.path.join(index_dir, f"{index_name}_vocab.pkl")
    docmap_path = os.path.join(index_dir, f"{index_name}_docmap.pkl")

    # Verificar si existe
    for path, label in [
        (index_path, "índice"),
        (vocab_path, "vocabulario"),
        (docmap_path, "doc_map"),
    ]:
        if not os.path.exists(path):
            print(f"Error: no se encontró el {label} en '{path}'")
            return

    # Cargar vocabulario en memoria
    print(f"Cargando vocabulario desde '{vocab_path}'...")
    vocabulary = cargar_vocabulario(vocab_path)
    doc_map = cargar_doc_map(docmap_path)
    print(f"  {len(vocabulary)} términos en vocabulario - {len(doc_map)} documentos")

    # Recuperar posting
    posting = recuperar_posting(term, vocabulary, doc_map, index_path)

    if posting is None:
        print(f"\nEl término '{term}' NO está en el vocabulario.")
    else:
        mostrar_posting(term, posting)


if __name__ == "__main__":
    main()
