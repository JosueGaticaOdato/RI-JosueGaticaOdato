"""
Compresion - VByte y Elias-GAmma
"""

import argparse
import os
import pickle
import struct
import time

from matplotlib import pyplot as plt

# --------------  CONSTANTES  -------------------

LEN_POSTING   =   8                   # 4 bytes para docID, 4 bytes para freq (2 * 4)
FMT_POSTING   =   ">2I"               # docID, freq
BASE_DIR      =   os.path.dirname(os.path.abspath(__file__))
OUT_DIR       =   "compressed_index"

# path_queries = os.path.join(BASE_DIR, "EFF-10K-queries.txt")
# # path_queries = os.path.join(BASE_DIR, "test.txt")
# path_stopwords = os.path.join(BASE_DIR, "stopwords.txt")

os.makedirs(os.path.join(BASE_DIR, OUT_DIR), exist_ok=True)

# ----------------- CODEC -----------------------

# ---------------- VBYTE ------------------------
def vbyte_encode(n: int) -> bytes:
    """Codifica un entero positivo con Variable Byte
      ultimos 7 bitss payload
      primer bit de continuacion o no
    """
    if n == 0:
        return bytes([0x80])          # 1000 0000
    buf = []
    while n > 0:
        buf.append(n & 0x7F)          # 7 bits payload
        n >>= 7
    buf[0] |= 0x80                    # último byte (MSB): continuation bit = 1
    return bytes(reversed(buf))


def vbyte_decode_stream(data: bytes) -> list[int]:
    """Decodifica todos los enteros VByte de un bloque de bytes."""
    
    result, current = [], 0
    for byte in data:
        if byte & 0x80:               # último byte del número
            current = (current << 7) | (byte & 0x7F)
            result.append(current)
            current = 0
        else:
            current = (current << 7) | byte
    return result

# ---------------- ELIAS ------------------------

class BitWriter:
    """Acumula bits y produce bytes al final."""
    def __init__(self):
        self._bits: list[int] = []

    def write_bits(self, value: int, n_bits: int):
        for i in range(n_bits - 1, -1, -1):
            self._bits.append((value >> i) & 1)

    def to_bytes(self) -> bytes:
        # pad a múltiplo de 8
        bits = self._bits[:]
        while len(bits) % 8:
            bits.append(0)
        out = bytearray()
        for i in range(0, len(bits), 8):
            byte = 0
            for b in bits[i:i+8]:
                byte = (byte << 1) | b
            out.append(byte)
        return bytes(out)

    def __len__(self):
        return len(self._bits)


class BitReader:
    """Lee bits de un bloque de bytes."""
    def __init__(self, data: bytes):
        self._bits = []
        for byte in data:
            for i in range(7, -1, -1):
                self._bits.append((byte >> i) & 1)
        self._pos = 0

    def read_bit(self) -> int:
        if self._pos >= len(self._bits):
            raise EOFError("BitReader: fin de stream")
        b = self._bits[self._pos]
        self._pos += 1
        return b

    def eof(self) -> bool:
        return self._pos >= len(self._bits)


def elias_gamma_encode(n: int) -> tuple[int, int]:
    """
    Devuelve (kd, kr) para n ≥ 1.
    kd = floor(log2(n)), kr = n - 2^kd
    """
    if n < 1:
        raise ValueError("Elias-γ requiere n ≥ 1")
    import math
    kd = int(math.floor(math.log2(n)))
    kr = n - (1 << kd)
    return kd, kr


def write_elias_gamma(bw: BitWriter, n: int):
    """Escribe Elias-γ(n) en el BitWriter (n ≥ 1)."""
    kd, kr = elias_gamma_encode(n)
    # kd ceros + 1 uno  (unario de kd)
    bw.write_bits(0, kd)
    bw.write_bits(1, 1)
    # kr en binario con kd bits
    if kd > 0:
        bw.write_bits(kr, kd)


def read_elias_gamma(br: BitReader) -> int:
    """Lee un número Elias-γ del BitReader."""
    kd = 0
    while br.read_bit() == 0:
        kd += 1
    # aquí ya leímos el '1'
    base = 1 << kd
    offset = 0
    for _ in range(kd):
        offset = (offset << 1) | br.read_bit()
    return base + offset

# --------------  FUNCIONES (EJ5) -------------------

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

# ------------------- DGAPS ------------------------

def apply_dgaps(docids: list[int]) -> list[int]:
    gaps = []
    prev = 0
    for d in docids:
        gaps.append(d - prev)
        prev = d
    return gaps


def invert_dgaps(gaps: list[int]) -> list[int]:
    docids, acc = [], 0
    for g in gaps:
        acc += g
        docids.append(acc)
    return docids

def recuperar_posting_list(term: str, meta_path: str, docid_path: str,
                          freq_path: str, use_dgaps: bool) -> list[tuple[int, int]]:
    """
    Recupera la posting list comprimida de un término
    """
    with open(meta_path, "rb") as f:
        meta = pickle.load(f)

    if term not in meta:
        return []

    df, d_off, f_off, d_nb, f_nb = meta[term]

    with open(docid_path, "rb") as fd:
        fd.seek(d_off)
        vb_data = fd.read(d_nb)

    values_d = vbyte_decode_stream(vb_data)
    docids = invert_dgaps(values_d) if use_dgaps else values_d

    with open(freq_path, "rb") as ff:
        ff.seek(f_off)
        g_data = ff.read(f_nb)

    br = BitReader(g_data)
    freqs = []
    for _ in range(df):
        if br.eof():
            break
        freqs.append(read_elias_gamma(br))

    return list(zip(docids, freqs))

# -------------------- MAIN --------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Recuperacion posting lists comprimida"
    )
    parser.add_argument("term",
        help='Término a buscar')
    parser.add_argument("--dgaps",
        choices=["dgaps", "nodgaps"],
        default="dgaps",
        help="Indica si el índice usa dgaps o nodgaps")
    
    args = parser.parse_args()

    use_dgaps = args.dgaps

    PATH = os.path.join(BASE_DIR, OUT_DIR) 

    docid_path = os.path.join(PATH, f"docids_{use_dgaps}.bin")
    freq_path  = os.path.join(PATH, f"freqs_{use_dgaps}.bin")
    meta_path  = os.path.join(PATH, f"vocab_{use_dgaps}.pkl")

    termino = args.term

    print(f"Recuperacion de la posting de {termino} comprimida")
    print(recuperar_posting_list(termino, meta_path, docid_path, freq_path,use_dgaps))


if __name__ == "__main__":
    main()