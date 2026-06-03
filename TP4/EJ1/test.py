"""
Prueba del ejercicio de BSBI visto en clase, con 4 docs
"""

import os
import pickle
import struct
from BSBI import bsbi_indexBuilder, LEN_POSTING

# Doc1 = ["casa", "casa", "perro"]
# Doc2 = ["gato", "auto", "perro"]
# Doc3 = ["gato", "perro", "gato"]
# Doc4 = ["auto", "casa", "perro"]

# corpus = [
#     (1, Doc1),
#     (2, Doc2),
#     (3, Doc3),
#     (4, Doc4),
# ]

Doc1 = ["casa", "perro", "casa"]
Doc2 = ["auto", "casa"]
Doc3 = ["gato", "perro"]

corpus = [
    (1, Doc1),
    (2, Doc2),
    (3, Doc3)
]

resultado = bsbi_indexBuilder(
    corpus=corpus,
    memoryLimit=4,
    index_root_path="prueba_bsbi",
    index_name="indice_prueba"
)

print(resultado)

# resultado = {
#     "vocab_path" : "prueba_bsbi\\indice_prueba_vocab.pkl",
#     "index_path" : "prueba_bsbi\\indice_prueba.bin"
# }

with open(resultado["vocab_path"], "rb") as f:
    vocab = pickle.load(f)

print("\nVOCABULARIO:")
print(vocab)

print("\nPOSTINGS:")
with open(resultado["index_path"], "rb") as f:
    for termino, (seek, df, term_id) in vocab.items():
        f.seek(seek)
        raw = f.read(df * LEN_POSTING)
        valores = struct.unpack(f">{df * 2}I", raw)
        postings = list(zip(valores[0::2], valores[1::2]))
        print(termino, postings)