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

