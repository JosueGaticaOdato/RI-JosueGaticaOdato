"""
Ejemplo de AND con Skip Lists - Demostración
Utiliza el ejemplo del README del ejercicio
"""

import math

def leer_posting_list_demo(posting_list):
    """Retorna lista de docIDs"""
    return posting_list


def armar_skip_list_demo(posting_list):
    """Calcula skip list con K = sqrt(len)"""
    if not posting_list:
        return []
    
    skip_list = []
    k = int(math.sqrt(len(posting_list)))
    if k < 1:
        k = 1
    
    for block_start in range(0, len(posting_list), k):
        block_end = min(block_start + k, len(posting_list))
        max_doc_id = posting_list[block_end - 1]
        skip_list.append((max_doc_id, block_start))
    
    return skip_list


def evaluar_consulta_demo(posting_corta, skip, posting_larga):
    """AND usando skip list"""
    resultado = []
    comparaciones_skip = 0
    comparaciones_secuencial = 0
    
    for target_docid in posting_corta:
        print(f"\n▶ Buscando docID = {target_docid}")
        
        # Usar skip list para encontrar bloque
        block_start = 0
        block_end = len(posting_larga)
        
        for i, (max_doc_id, block_offset) in enumerate(skip):
            comparaciones_skip += 1
            print(f"  Comparar {max_doc_id} < {target_docid}?", end=" ")
            
            if max_doc_id < target_docid:
                print(f"Sí → saltar bloque, pasar al siguiente")
                block_start = block_offset
                # Calcular el fin del bloque (donde comienza el siguiente)
                if i + 1 < len(skip):
                    block_end = skip[i + 1][1]
                else:
                    # Último bloque de la skip list
                    block_end = len(posting_larga)
            else:
                print(f"No → buscar en este bloque")
                block_start = block_offset
                # Calcular el fin del bloque (donde comienza el siguiente)
                if i + 1 < len(skip):
                    block_end = skip[i + 1][1]
                else:
                    # Último bloque de la skip list
                    block_end = len(posting_larga)
                break
        
        # Búsqueda secuencial
        print(f"  Bloque a revisar: {posting_larga[block_start:block_end]}")
        encontrado = False
        for j in range(block_start, block_end):
            comparaciones_secuencial += 1
            print(f"    Comparar {posting_larga[j]} == {target_docid}?", end=" ")
            if posting_larga[j] == target_docid:
                print("✓ ENCONTRADO")
                resultado.append(target_docid)
                encontrado = True
                break
            elif posting_larga[j] > target_docid:
                print(f"✗ (y {posting_larga[j]} > {target_docid}) → no existe")
                break
            else:
                print("✗")
    
    return {
        "resultado": resultado,
        "comparaciones_skip": comparaciones_skip,
        "comparaciones_secuencial": comparaciones_secuencial
    }


# Datos del ejemplo del README
perro = [7, 18, 31, 52, 60, 83, 104, 135]
casa = [3, 5, 7, 12, 18, 20, 25, 31, 37, 45, 50, 52, 55, 60, 68, 75, 83, 90, 104, 110, 120, 135, 150, 180]

print("="*70)
print("EJEMPLO DE AND CON SKIP LISTS")
print("="*70)

print(f"\nTérmino 'perro' (corto): {len(perro)} docs")
print(f"  DocIDs: {perro}")

print(f"\nTérmino 'casa' (largo): {len(casa)} docs")
print(f"  DocIDs: {casa}")

# Calcular skip list de casa
skip_casa = armar_skip_list_demo(casa)
k = int(math.sqrt(len(casa)))
print(f"\nK (tamaño de bloque): {k}")
print(f"\nSkip List de 'casa':")
for max_doc_id, block_start in skip_casa:
    print(f"  ({max_doc_id}, {block_start})")

print("\n" + "="*70)
print("BÚSQUEDA: perro AND casa")
print("="*70)

resultado = evaluar_consulta_demo(perro, skip_casa, casa)

print("\n" + "="*70)
print("RESULTADO")
print("="*70)
print(f"DocIDs encontrados: {resultado['resultado']}")
print(f"Comparaciones skip list: {resultado['comparaciones_skip']}")
print(f"Comparaciones secuencial: {resultado['comparaciones_secuencial']}")
print(f"Total comparaciones: {resultado['comparaciones_skip'] + resultado['comparaciones_secuencial']}")
print(f"\nObservación: Sin skip list, necesitaríamos {len(casa)} comparaciones.")
print(f"Con skip list optimizamos a {resultado['comparaciones_skip'] + resultado['comparaciones_secuencial']} comparaciones.")
