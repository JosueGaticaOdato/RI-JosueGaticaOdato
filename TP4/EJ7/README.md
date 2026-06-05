# Ejercicio 7

Comprima el índice del ejercicio 1 utilizando Variable-Length Codes (VByte) para los docIDs y Elias-gamma para las frecuencias (almacene docIDs y frecuencias en archivos separados). Calcule tiempos de compresión/descompresión del índice completo y tamaño resultante en cada caso. Realice dos experimentos, con y sin DGaps. Compare los tamaños de los índices resultantes.

## Ejecucicion del script con el indice de la coleccion Snapshot de Wikipedia (small)
```bash
python TP4/EJ7/EJ7.py --index-dir TP4/index-small --index-name index-small
```

## Ejecucicion del script con el indice de la coleccion Snapshot de Wikipedia (run)
```bash
python TP4/EJ7/EJ7.py --index-dir TP4/index-large --index-name index-large
```

# 7.1

Agregue un script que permita recuperar de disco la posting list de un término  dado y la versión comprimida de dicha lista.

## Ejecucicion del script con el indice de la coleccion Snapshot de Wikipedia (small)
```bash
python TP4/EJ7/EJ7-1.py "encyclopedia" --dgaps dgaps
python TP4/EJ7/EJ7-1.py "encyclopedia" --dgaps nodgaps
```

## Ejecucicion del script con el indice de la coleccion Snapshot de Wikipedia (run)
```bash
python TP4/EJ7/EJ7-1.py "encyclopedia" --dgaps dgaps
python TP4/EJ7/EJ7-1.py "encyclopedia" --dgaps nodgaps
```