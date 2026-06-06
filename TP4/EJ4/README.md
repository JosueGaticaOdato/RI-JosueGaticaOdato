# Ejercicio 4

Codifique un script que implemente la estrategia DAAT vista en clase y sobre el índice creado en el ejercicio 1 permita resolver consultas usando el modelo vectorial utilizando la métrica del coseno como medida de similitud. Dada una consulta su script debe retornar los top-k documentos de score mayor. 

Su script debe mostrar como salida el nombre, el docID y el score (ordenado por score) con el siguiente formato 

DocName:docID:Score

## Prueba con coleccion vista en clase

```bash
python TP4/EJ4/EJ4.py "casa" --index-dir TP4/EJ1/index_debug --index-name index_debug -k 3
python TP4/EJ4/EJ4.py "casa perro" --index-dir TP4/EJ1/index_debug --index-name index_debug -k 2
python TP4/EJ4/EJ4.py "casa perro gato)" --index-dir TP4/EJ1/index_debug --index-name index_debug -k 2
```

## Ejecucicion del script con el indice de la coleccion Snapshot de Wikipedia (small)
```bash
python TP4/EJ4/EJ4.py "spirit encyclopedia article" --index-dir TP4/index-small --index-name index-small -k 5
python TP4/EJ4/EJ4.py "states democracy article"--index-dir TP4/index-small --index-name index-small -k 5
```

## Ejecucicion del script con el indice de la coleccion Snapshot de Wikipedia (run)
```bash
python TP4/EJ4/EJ4.py "spirit encyclopedia article" --index-dir TP4/index-large --index-name index-large -k 5
python TP4/EJ4/EJ4.py "states democracy article" --index-dir TP4/index-large --index-name index-large -k 5
```