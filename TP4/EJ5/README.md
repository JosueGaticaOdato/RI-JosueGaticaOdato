# Ejercicio 5

Agregue skip lists a su índice del ejercicio 1 y ejecute un conjunto de consultas AND sobre el índice original y luego usando los punteros. Compare los tiempos de ejecución con los del ejercicio 3. 

```bash
python TP4/EJ5/EJ5.py "casa" "perro" --index-dir TP4/EJ1/index_debug --index-name index_debug
```

## Ejecucicion del script con el indice de la coleccion Snapshot de Wikipedia (small)
```bash
python TP4/EJ5/EJ5.py "spirit" "encyclopedia" --index-dir TP4/index-small --index-name index-small
python TP4/EJ5/EJ5.py "states" "article" --index-dir TP4/index-small --index-name index-small
```

## Ejecucicion del script con el indice de la coleccion Snapshot de Wikipedia (run)
```bash
python TP4/EJ5/EJ5.py "spirit" "encyclopedia" --index-dir TP4/index-large --index-name index-large
python TP4/EJ5/EJ5.py "states" "article" --index-dir TP4/index-large --index-name index-large
```


# 5.1

Agregue un script que permita recuperar las skips list para un término dado. En este caso la salida deberá ser una lista de docName:docID ordenada por docName.

Utilice la colección para debugging para calibrar su script.

## Prueba con coleccion vista en clase

```bash
python TP4/EJ5/EJ5-1.py "casa" --index-dir TP4/EJ1/index_debug --index-name index_debug
```

## Ejecucicion del script con el indice de la coleccion Snapshot de Wikipedia (small)
```bash
python TP4/EJ5/EJ5-1.py "encyclopedia" --index-dir TP4/index-small --index-name index-small
python TP4/EJ5/EJ5-1.py "states" --index-dir TP4/index-small --index-name index-small
```

## Ejecucicion del script con el indice de la coleccion Snapshot de Wikipedia (run)
```bash
python TP4/EJ5/EJ5-1.py "encyclopedia" --index-dir TP4/index-large --index-name index-large
python TP4/EJ5/EJ5-1.py "states" --index-dir TP4/index-large --index-name index-large
```

