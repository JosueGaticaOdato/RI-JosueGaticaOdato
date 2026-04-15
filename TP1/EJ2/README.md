# Ejercicio 2

Escriba un programa que realice análisis léxico sobre la colección RI-tknz-data. El programa debe recibir como parámetros el directorio donde se encuentran los documentos y un argumento que indica si se deben eliminar las palabras vacías (y en tal caso, el nombre del archivo que las contiene). Defina, además, una longitud mínima y máxima para los términos. Como salida, el programa debe generar:

* Un archivo (terminos.txt) con la lista de términos a indexar (ordenado), su frecuencia en la colección y su DF (Document Frequency).

  Formato de salida: $<termino> [ESP] <CF> [ESP] <DF>$. 

  Ejemplo:
	* casa 238 3
	* perro 644 6
	* ...
	* zorro 12 1

* Un segundo archivo (estadisticas.txt) con los siguientes datos (un ítem por línea y separados por espacio cuando sean más de un valor):
    * Cantidad de documentos procesados.
    * Cantidad de tokens y términos extraídos.
    * Promedio de tokens y términos de los documentos.
    * Largo promedio de un término.
    * Cantidad de tokens y términos del documento más corto y del más largo.
    * Cantidad de términos que aparecen sólo 1 vez en la colección.

* Un tercer archivo (frecuencias.txt), con: 
    * La lista de los 10 términos más frecuentes y su CF (Collection Frequency). Un término por línea.
    * La lista de los 10 términos menos frecuentes y su CF. Un término por línea.


## Comando a ejecutar

La ruta del archivo comienzo desde la carpeta donde estamos ubicados

```bash
python EJ2.py ../Colecciones/RI-tknz-data
```

Con stopwords:

```bash
python EJ2.py ../Colecciones/RI-tknz-data stopwords.txt
```