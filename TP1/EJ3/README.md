# Ejercicio 3

Escriba un segundo tokenizer que implemente los criterios del artículo de Grefenstette y Tapanainen para definir qué es una “palabra” (o término) y cómo tratar números y signos de puntuación. En este  caso  su  tokenizer deberá extraer y tratar como un único término: 

*	Abreviaturas tal cual están escritas (por ejemplo, Dr., Lic., S.A., etc.) 
*	Direcciones de correo electrónico y URLs.
*	Números (por ejemplo, cantidades, teléfonos).
*	Nombres propios (por ejemplo, Villa Carlos Paz, Manuel Belgrano, etc.)
 
Utilice la colección para debugging  de expresiones regulares provista por el equipo docente para extraer y comparar  la salida de su programa con los metadatos de la colección tal como lo realizó en el punto 1.

Por último, extraiga y almacene la misma información que en el punto 2 sobre la colección RI-tknz-data utilizando su nuevo tokenizer.

## Comando a ejecutar

La ruta del archivo comienzo desde la carpeta donde estamos ubicados

```bash
python EJ3.py ../Colecciones/RI-tknz-data
```

Con stopwords:

```bash
python EJ3.py ../Colecciones/RI-tknz-data stopwords.txt
```