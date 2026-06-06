# Ejercicio 3

Utilizando el código e índice anteriores ejecute corridas  con el siguiente subset de queries (filtre solo los de 2 y 3 términos que estén en el vocabulario de su colección) y mida el tiempo de ejecución en cada caso. Para ello, utilice los siguientes patrones booleanos:

A.	Queries |q| = 2
*	t1 AND t2
*	t1 OR t2
*	t1 NOT t2

B.	Queries |q| = 3
*	t1 AND t2 AND t3
*	(t1 OR t2) NOT t3
*	(t1 AND t2) OR t3

¿Puede relacionar los tiempos de ejecución con los tamaños de las listas? (pruebe con el índice en disco o cargándolo completamente en memoria antes). ¿Qué conclusiones se pueden extraer?

## Prueba con coleccion vista en clase

```bash
python TP4/EJ3/EJ3.py --index-dir TP4/EJ1/index_debug --index-name index_debug
```

## Ejecucicion del script con el indice de la coleccion Snapshot de Wikipedia (small)
```bash
python TP4/EJ3/EJ3.py --index-dir TP4/index-small --index-name index-small
python TP4/EJ3/EJ3.py --index-dir TP4/index-small --index-name index-small
```

## Ejecucicion del script con el indice de la coleccion Snapshot de Wikipedia (run)
```bash
python TP4/EJ3/EJ3.py --index-dir TP4/index-large --index-name index-large
python TP4/EJ3/EJ3.py --index-dir TP4/index-large --index-name index-large
```

