"""
DAAT para Ranking

Consultas con modelo vectorial utilizando metrica del coseno

"""

# --------------  CONSTANTES  -------------------

import pickle
import struct


LEN_POSTING = 8

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


def leer_posting(term, vocabulario, index_path):
    """
    Lee la posting list de un término desde disco
    """
    if term not in vocabulario:
        return [], []

    df, seek = vocabulario[term]
    with open(index_path, "rb") as f:
        f.seek(seek)
        raw = f.read(df * LEN_POSTING)

    unpacked = struct.unpack(f">{df * 2}I", raw)
    docids = list(unpacked[0::2])
    freqs = list(unpacked[1::2])
    return docids, freqs