# Ejercicio 5

Escriba un script que lea un directorio con documentos de texto y arme una estructura de datos en memoria para soportar la recuperación. Luego, debe permitir ingresar una consulta y devolver un ranking de los documentos relevantes utilizando el modelo vectorial. Use TF/IDF según MIR [1]: (1 + log(freqi,j)) x log (N / ni) 
	
# Ejercicio 5.1

Indexe la colección del ejercicio 4 con su software. Ejecute las consultas y compare los resultados con los obtenidos con pyTerrier. ¿Son consistentes?

## Comando a ejecutar

La ruta del archivo comienza desde la carpeta donde estamos ubicados

```bash
python EJ5.py
```