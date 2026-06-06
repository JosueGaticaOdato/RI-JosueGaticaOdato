# Ejercicio 2

Codifique un script que implemente la estrategia TAAT vista en clase y sobre el índice creado en el ejercicio 1 permita realizar operaciones sobre conjuntos para buscar por dos o tres términos utilizando los operadores AND, OR y NOT. 
Su script debe permitir el procesamiento de consultas del tipo:

((t1 AND t2) OR t3) 
((t1 AND NOT t2) OR NOT T3))

Como salida su script debe retornar el nombre y el docID de los documentos que satisfacen la consulta.

## Prueba con coleccion vista en clase

```bash
python TP4/EJ2/EJ2.py "((casa AND perro) OR casa)" --index-dir TP4/EJ1/index_debug --index-name index_debug
python TP4/EJ2/EJ2.py "(casa AND auto)" --index-dir TP4/EJ1/index_debug --index-name index_debug
python TP4/EJ2/EJ2.py "((casa AND auto) OR gato)" --index-dir TP4/EJ1/index_debug --index-name index_debug
```

## Ejecucicion del script con el indice de la coleccion Snapshot de Wikipedia (small)
```bash
python TP4/EJ2/EJ2.py "((spirit AND encyclopedia) AND article)" --index-dir TP4/index-small --index-name index-small
python TP4/EJ2/EJ2.py "(spirit AND encyclopedia)" --index-dir TP4/index-small --index-name index-small
python TP4/EJ2/EJ2.py "((states AND democracy) AND NOT article))" --index-dir TP4/index-small --index-name index-small
```

## Ejecucicion del script con el indice de la coleccion Snapshot de Wikipedia (run)
```bash
python TP4/EJ2/EJ2.py "((spirit AND encyclopedia) OR article)" --index-dir TP4/index-large --index-name index-large
python TP4/EJ2/EJ2.py "(spirit AND encyclopedia)" --index-dir TP4/index-large --index-name index-large
python TP4/EJ2/EJ2.py "((spirit AND NOT encyclopedia) OR NOT article))" --index-dir TP4/index-large --index-name index-large
```
