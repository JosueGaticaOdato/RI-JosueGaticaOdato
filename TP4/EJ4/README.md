# Ejercicio 4

Codifique un script que implemente la estrategia DAAT vista en clase y sobre el índice creado en el ejercicio 1 permita resolver consultas usando el modelo vectorial utilizando la métrica del coseno como medida de similitud. Dada una consulta su script debe retornar los top-k documentos de score mayor. 

Su script debe mostrar como salida el nombre, el docID y el score (ordenado por score) con el siguiente formato 

DocName:docID:Score

## Prueba con coleccion vista en clase

```bash
python TP4/EJ2/EJ2.py "((casa AND perro) OR casa)" --index-dir TP4/EJ1/index_debug --index-name index_debug
python TP4/EJ2/EJ2.py "(casa AND auto)" --index-dir TP4/EJ1/index_debug --index-name index_debug
python TP4/EJ2/EJ2.py "((casa AND auto) OR gato)" --index-dir TP4/EJ1/index_debug --index-name index_debug
```

