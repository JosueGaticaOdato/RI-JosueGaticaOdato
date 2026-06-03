# Ejercicio 1

Codifique un script que indexe una colección que requiera el volcado parcial a disco (asumiendo que existe un límite de memoria) implementando el método  BSBI visto en clase. Para esto su script debe recibir un parámetro n que indica cada cuántos documentos se debe hacer el volcado a disco. Al finalizar, debe unir (merge) los índices parciales. Para las pruebas use la colección snapshot de Wikipedia y varios valores de n (por ejemplo, n = 10% del tamaño de la colección). Registre los tiempos de indexación y de merge por separado. Grafique la distribución de tamaños de las posting lists. Calcule el overhead de su índice respecto de la colección. ¿Qué conclusiones se pueden extraer?


## Prueba con coleccion vista en clase
```bash
python TP4/EJ1/EJ1.py TP4/EJ1/coleccion_debug -n 4 --index-dir TP4/EJ1/index_debug --index-name index_debug
```

## Ejecucion con coleccion de Snapshot de Wikipedia (Test)
```bash
python TP4/EJ1/EJ1.py TP4/Colecciones/test -n 2 --index-dir TP4/EJ1/index_test --index-name index_test
```

## Ejecucion con coleccion de Snapshot de Wikipedia
```bash
python TP4/EJ1/EJ1.py TP4/Colecciones/en/articles -n 10 --index-dir TP4/EJ1/index --index-name index
```

# 1.1

Agregue un script que cargue el vocabulario de la colección en memoria, permita recuperar una posting completa de un término y la muestre por pantalla. Para cada documento retornado se deberá mostrar el nombre, el  docID asignado  durante la creación del índice y la frecuencia en el siguiente formato: 

DocName:docID:Frecuencia

Utilice la colección de debug para calibrar su script y verificar que la salida sea correcta.

## Ejecucicion del script con el indice de la coleccion vista en clase
```bash
python TP4/EJ1/EJ1-Posting.py casa --index-dir TP4/EJ1/index_debug --index-name index_debug
```

## Ejecucicion del script con el indice de la coleccion Snapshot de Wikipedia (Test)
```bash
python TP4/EJ1/EJ1-Posting.py Wikipedia --index-dir TP4/EJ1/index_test --index-name index_test
```

## Ejecucicion del script con el indice de la coleccion Snapshot de Wikipedia
```bash
python TP4/EJ1/EJ1-Posting.py Wikipedia --index-dir TP4/EJ1/index --index-name index
```
