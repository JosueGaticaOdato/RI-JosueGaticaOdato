"""
Funcion para llevar a cabo la construcion del indice
"""

import argparse
from BSBI import build_index

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

    build_index(
        collection_path=args.collection,
        n=args.block_size,
        chunks_dir=args.index_dir,
        index_name=args.index_name,
    )