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

# ------------------- COMPRESION ---------------------

def compress_index(use_dgaps: bool, vocab: dict, index_path) -> dict:
    """
    Comprime el índice completo.
    Retorna metadata: {term: (df, docid_offset, freq_offset, docid_nbytes, freq_nbytes)}
    Archivos de salida:
      - compressed_index/docids_{tag}.bin   (VByte)
      - compressed_index/freqs_{tag}.bin    (Elias)
      - compressed_index/vocab_{tag}.pkl    (metadata)
    """
    tag = "dgaps" if use_dgaps else "nodgaps"
    docid_path = os.path.join(os.path.join(BASE_DIR, OUT_DIR), f"docids_{tag}.bin")
    freq_path  = os.path.join(os.path.join(BASE_DIR, OUT_DIR), f"freqs_{tag}.bin")
    meta_path  = os.path.join(os.path.join(BASE_DIR, OUT_DIR), f"vocab_{tag}.pkl")

    meta = {}
    docid_offset = 0
    freq_offset  = 0

    t0 = time.perf_counter()

    with open(docid_path, "wb") as fd, open(freq_path, "wb") as ff:
        for term, (df, _) in vocab.items():
            postings = leer_posting_list(term, vocab, index_path)
            docids = [p[0] for p in postings]
            freqs  = [p[1] for p in postings]

            # --------------- VByte para docIDs ---------------
            if use_dgaps:
                values_d = apply_dgaps(docids)
            else:
                values_d = docids

            vbyte_data = b"".join(vbyte_encode(v) for v in values_d)
            fd.write(vbyte_data)

            # ------------  Elias-γ para frecuencias ----------
            bw = BitWriter()
            for f_val in freqs:
                write_elias_gamma(bw, f_val)
            gamma_data = bw.to_bytes()
            ff.write(gamma_data)

            meta[term] = (df, docid_offset, freq_offset,
                          len(vbyte_data), len(gamma_data))
            docid_offset += len(vbyte_data)
            freq_offset  += len(gamma_data)

    t_compress = time.perf_counter() - t0

    with open(meta_path, "wb") as fm:
        pickle.dump(meta, fm)

    sizes = {
        "docids_bytes": os.path.getsize(docid_path),
        "freqs_bytes":  os.path.getsize(freq_path),
        "t_compress":   t_compress,
    }
    return sizes, meta_path, docid_path, freq_path

# ------------------- DESCOMPRIMIR ---------------------

def decompress_index(meta_path: str, docid_path: str, freq_path: str,
                     use_dgaps: bool) -> float:
    """Descomprime el índice completo y retorna el tiempo."""
    with open(meta_path, "rb") as f:
        meta = pickle.load(f)

    t0 = time.perf_counter()
    with open(docid_path, "rb") as fd, open(freq_path, "rb") as ff:
        for term, (df, d_off, f_off, d_nb, f_nb) in meta.items():
            # docIDs
            fd.seek(d_off)
            vb_data = fd.read(d_nb)
            values_d = vbyte_decode_stream(vb_data)

            if use_dgaps:
                docids = invert_dgaps(values_d)
            else:
                docids = values_d

            # frecuencias
            ff.seek(f_off)
            g_data = ff.read(f_nb)
            br = BitReader(g_data)
            freqs = []
            for _ in range(df):
                if br.eof():
                    break
                freqs.append(read_elias_gamma(br))

    return time.perf_counter() - t0

# ------------- Unidades -------------------

def fmt_bytes(b: int) -> str:
    if b < 1024:
        return f"{b} B"
    elif b < 1024**2:
        return f"{b/1024:.2f} KB"
    return f"{b/1024**2:.2f} MB"

# ------------- Graficos  -------------------

def graficos(results, orig_size, output_dir="graficos"):
    os.makedirs(output_dir, exist_ok=True)

    labels = list(results.keys())

    docids = [results[k]["docids_bytes"] for k in labels]
    freqs  = [results[k]["freqs_bytes"] for k in labels]
    total  = [results[k]["total_comp"] for k in labels]

    ratios = [results[k]["ratio"] for k in labels]
    saving = [results[k]["saving"] * 100 for k in labels]

    compress_time = [results[k]["t_compress"] for k in labels]
    decompress_time = [results[k]["t_decompress"] for k in labels]

    # Tamaño índice
    plt.figure()
    plt.bar(labels, total, label="Comprimido")
    plt.axhline(orig_size, linestyle="--", label="Original")
    plt.title("Tamaño del índice")
    plt.ylabel("Bytes")
    plt.legend()
    plt.savefig(os.path.join(output_dir, "1_tamanio_indice.png"), dpi=200, bbox_inches="tight")
    plt.close()

    # DocIDs vs Freqs
    plt.figure()
    plt.bar(labels, docids, label="DocIDs (VByte)")
    plt.bar(labels, freqs, bottom=docids, label="Freqs (Elias-γ)")
    plt.title("Desglose del índice comprimido")
    plt.ylabel("Bytes")
    plt.legend()
    plt.savefig(os.path.join(output_dir, "2_desglose.png"), dpi=200, bbox_inches="tight")
    plt.close()

    # Ratio compresión
    plt.figure()
    plt.bar(labels, ratios)
    plt.title("Ratio de compresión (Original / Comprimido)")
    plt.ylabel("x")
    plt.savefig(os.path.join(output_dir, "3_ratio.png"), dpi=200, bbox_inches="tight")
    plt.close()

    # Ahorro de espacio
    plt.figure()
    plt.bar(labels, saving)
    plt.title("Ahorro de espacio (%)")
    plt.ylabel("%")
    plt.savefig(os.path.join(output_dir, "4_ahorro.png"), dpi=200, bbox_inches="tight")
    plt.close()

    # Tiempos
    plt.figure()
    plt.bar(labels, compress_time, label="Compresión")
    plt.bar(labels, decompress_time, bottom=compress_time, label="Descompresión")
    plt.title("Tiempos de procesamiento")
    plt.ylabel("Segundos")
    plt.legend()
    plt.savefig(os.path.join(output_dir, "5_tiempos.png"), dpi=200, bbox_inches="tight")
    plt.close()

# -------------------- MAIN --------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Compresion"
    )
    parser.add_argument("--index-dir",
        help="Directorio del índice")
    parser.add_argument("--index-name",
        help="Nombre base del índice")
    
    args = parser.parse_args()

    vocabulary, doc_map = cargar_indice(args.index_dir, args.index_name)
    index_path = os.path.join(args.index_dir, f"{args.index_name}.bin")

    print("Compresion del indice con VByte (docID) y Elias (freq)")
    print(f"Nombre del indice: {args.index_name}")
    print(f"({len(vocabulary):,} términos, {len(doc_map):,} docs)")

    orig_size = os.path.getsize(index_path)
    print(f"Tamaño índice original: {fmt_bytes(orig_size)}")

    results = {}

    for use_dgaps in (False, True):
        tag   = "CON DGaps" if use_dgaps else "SIN DGaps"
        stag  = "dgaps"    if use_dgaps else "nodgaps"
        print(f"\n{'─'*62}")
        print(f"  {tag}")
        print(f"{'─'*62}")

        print("  [1/2] Comprimiendo...", end=" ", flush=True)
        sizes, meta_path, docid_path, freq_path = compress_index(use_dgaps, vocabulary, index_path)
        print(f"listo en {sizes['t_compress']:.3f}s")

        print("  [2/2] Descomprimiendo...", end=" ", flush=True)
        t_dec = decompress_index(meta_path, docid_path, freq_path, use_dgaps)
        print(f"listo en {t_dec:.3f}s")

        total_comp = sizes["docids_bytes"] + sizes["freqs_bytes"]
        ratio      = orig_size / total_comp
        saving     = 1 - total_comp / orig_size

        print(f"\n  Tamaño docIDs  (VByte):  {fmt_bytes(sizes['docids_bytes'])}")
        print(f"  Tamaño freqs   (Elias-γ): {fmt_bytes(sizes['freqs_bytes'])}")
        print(f"  Total comprimido:         {fmt_bytes(total_comp)}")
        print(f"  Tasa de compresión:       {ratio:.2f}x")
        print(f"  Ahorro de espacio:        {saving*100:.1f}%")
        print(f"  Tiempo compresión:        {sizes['t_compress']:.3f}s")
        print(f"  Tiempo descompresión:     {t_dec:.3f}s")

        # results[stag] = {
        #     "meta": meta_path, "docids": docid_path, "freqs": freq_path,
        #     "use_dgaps": use_dgaps, "total_comp": total_comp,
        # }
        results[stag] = {
            "use_dgaps": use_dgaps,
            "docids_bytes": sizes["docids_bytes"],
            "freqs_bytes": sizes["freqs_bytes"],
            "total_comp": total_comp,
            "orig_size": orig_size,
            "ratio": ratio,
            "saving": saving,
            "t_compress": sizes["t_compress"],
            "t_decompress": t_dec
        }

    graficos(results, orig_size, output_dir="output_graficos")

if __name__ == "__main__":
    main()