# Ejercicio 1

Codifique un script que indexe una colección que requiera el volcado parcial a disco (asumiendo que existe un límite de memoria) implementando el método  BSBI visto en clase. Para esto su script debe recibir un parámetro n que indica cada cuántos documentos se debe hacer el volcado a disco. Al finalizar, debe unir (merge) los índices parciales. Para las pruebas use la colección snapshot de Wikipedia y varios valores de n (por ejemplo, n = 10% del tamaño de la colección). Registre los tiempos de indexación y de merge por separado. Grafique la distribución de tamaños de las posting lists. Calcule el overhead de su índice respecto de la colección. ¿Qué conclusiones se pueden extraer?

## Creacion del indice (EJ1.py)

### Comando de ejecucion

```bash
python TP4/EJ1/EJ1.py [-h] [-n BLOCK_SIZE] [--index-dir INDEX_DIR] [--index-name INDEX_NAME] collection
```

Prueba con coleccion vista en clase
```bash
python TP4/EJ1/EJ1.py TP4/Colecciones/coleccion_debug -n 4 --index-dir TP4/EJ1/index_debug --index-name index_debug
```

Creacion del indice con coleccion de Snapshot de Wikipedia (debug)
```bash
python TP4/EJ1/EJ1.py TP4/Colecciones/wiki-small/en/articles -n 300000 --index-dir TP4/index-small --index-name index-small
```

Creacion del indice con coleccion de Snapshot de Wikipedia (run)
```bash
python TP4/EJ1/EJ1.py TP4/Colecciones/wiki-large/en/articles -n 300000  --index-dir TP4/index-large --index-name index-large
```

## Evaluacion con diferentes valores de N (BSBI_Analisis.py)

Prueba con coleccion vista en clase
```bash
python TP4/EJ1/BSBI_Analisis.py TP4/Colecciones/coleccion_debug --index-dir TP4/EJ1/index-analisis 
```

Ejecucion con coleccion de Snapshot de Wikipedia (debug)
```bash
python TP4/EJ1/BSBI_Analisis.py TP4/Colecciones/wiki-small/en/articles --index-dir TP4/EJ1/index-analisis-wiki-small
```

# 1.1

Agregue un script que cargue el vocabulario de la colección en memoria, permita recuperar una posting completa de un término y la muestre por pantalla. Para cada documento retornado se deberá mostrar el nombre, el  docID asignado  durante la creación del índice y la frecuencia en el siguiente formato: 

DocName:docID:Frecuencia

Utilice la colección de debug para calibrar su script y verificar que la salida sea correcta.

### Comando de ejecucion

```bash
python EJ1-Posting.py [-h] [--index-dir INDEX_DIR] [--index-name INDEX_NAME] term
```

Ejecucicion del script con el indice de la coleccion vista en clase
```bash
python TP4/EJ1/EJ1-Posting.py casa --index-dir TP4/EJ1/index_debug --index-name index_debug
```

Ejecucicion del script con el indice de la coleccion Snapshot de Wikipedia (Test)
```bash
python TP4/EJ1/EJ1-Posting.py encyclopedia --index-dir TP4/EJ1/index_test --index-name index_test
```

Ejecucicion del script con el indice de la coleccion Snapshot de Wikipedia (small)
```bash
python TP4/EJ1/EJ1-Posting.py encyclopedia --index-dir TP4/index-small --index-name index-small
python TP4/EJ1/EJ1-Posting.py spirit --index-dir TP4/index-small --index-name index-small
```

Ejecucicion del script con el indice de la coleccion Snapshot de Wikipedia (run)
```bash
python TP4/EJ1/EJ1-Posting.py encyclopedia --index-dir TP4/index-large --index-name index-large
python TP4/EJ1/EJ1-Posting.py spirit --index-dir TP4/index-large --index-name index-large
```