"""
Funcion para llevar a cabo la construcion del indice
"""

import argparse
import os
from bs4 import BeautifulSoup
from BSBI import build_index

# -------- Wiki-Small procesamiento (Tomado de TP2/EJ4)  -------------

def extract_text_from_html(filepath:str):
  with open(filepath, "r", encoding="utf-8") as file:
    soup = BeautifulSoup(file,"html.parser")
    return soup.get_text(separator=" ", strip= True)

def process_wiki_collection(root_dir: str) -> dict:
    documents = {}

    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:

            full_path = os.path.join(dirpath, filename)
            relative_path = os.path.relpath(full_path, root_dir)

            try:
                # CASO HTML
                if filename.endswith(".html"):
                    text = extract_text_from_html(full_path)

                # CASO TXT
                elif filename.endswith(".txt"):
                    with open(full_path, "r", encoding="utf-8") as f:
                        text = f.read()

                else:
                    continue

                documents[relative_path] = text

            except Exception as e:
                print(f"Error leyendo {full_path}: {e}")

    return documents

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
    parser.add_argument("--index-name", default="index",
                        help="Nombre base del índice")
    args = parser.parse_args()

    collection_path = args.collection
    index_dir = args.index_dir
    n = args.block_size
    index_name = args.index_name

    # Procesamiento de la coleccion
    print("Procesando coleccion...")
    archivos = sorted(process_wiki_collection(collection_path))
    corpus = [
      (docid, os.path.join(collection_path, archivo))
      for docid, archivo in enumerate(archivos, start=1)
    ]
    total_docs = len(archivos)
    print(f"Colección: {total_docs} documentos en '{collection_path}'")

    # Construir el indice
    build_index(
        corpus=corpus,
        collection_path=collection_path,
        n=n,
        chunks_dir=index_dir,
        index_name=index_name,
    )