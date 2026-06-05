"""
Ejemplo de Skip List - Demostración numérica
Según el ejemplo del README del ejercicio
"""

# Ejemplo del README:
# DocIDs: [9, 33, 45, 50, 64, 66, 72, 100, 123, 200, 250]
# N = 11
# K = 3

docids = [9, 33, 45, 50, 64, 66, 72, 100, 123, 200, 250]
K = 3

print(f"DocIDs: {docids}")
print(f"N = {len(docids)}")
print(f"K = {K}")
print()

# Dividir en bloques
print("Bloques:")
bloques = []
for block_start in range(0, len(docids), K):
    block_end = min(block_start + K, len(docids))
    bloque = docids[block_start:block_end]
    bloques.append(bloque)
    print(f"  Bloque {len(bloques)}: {bloque}")

print()

# Calcular skip list
print("Skip list (maxDocID, offset):")
skip_list = []
for block_num, bloque in enumerate(bloques):
    max_doc_id = bloque[-1]
    offset = (block_num + 1) * K  # offset al siguiente bloque
    skip_list.append((max_doc_id, offset))
    print(f"  ({max_doc_id}, {offset})")

print()

# Ejemplo de búsqueda
target = 100
print(f"Búsqueda de docID = {target}:")
print()

comparaciones_skip = 0
bloques_saltados = 0

for max_doc_id, offset in skip_list:
    comparaciones_skip += 1
    print(f"  Comparar {max_doc_id} < {target}?", end=" ")
    if max_doc_id < target:
        print("Sí → puedo saltar este bloque")
        bloques_saltados += 1
    else:
        print("No → STOP, buscar secuencialmente aquí")
        break

print()
print(f"Comparaciones skip list: {comparaciones_skip}")
print(f"Bloques saltados: {bloques_saltados}")
print()

# Búsqueda secuencial en el bloque
block_idx = bloques_saltados
if block_idx < len(bloques):
    bloque = bloques[block_idx]
    print(f"Bloque a revisar: {bloque}")
    comparaciones_secuencial = 0
    for docid in bloque:
        comparaciones_secuencial += 1
        print(f"  Comparar {docid} == {target}?", end=" ")
        if docid == target:
            print("Sí → ENCONTRADO!")
            break
        elif docid > target:
            print(f"No (y {docid} > {target}) → No existe")
            break
        else:
            print("No")
    
    print()
    print(f"Comparaciones secuencial: {comparaciones_secuencial}")
    print(f"Total comparaciones: {comparaciones_skip + comparaciones_secuencial}")
