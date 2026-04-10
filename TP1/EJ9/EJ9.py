import re, sys

def tokenizer(texto):
  return re.findall(r"[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ]+", texto.lower()) # Minusculas y acento español

def guardar_pares(tokens, paso = 100):
   
  vocabulario = set()
  pares = []

  for i, token in enumerate(tokens, start=1):
      vocabulario.add(token)
      
      if i % paso == 0:
          pares.append((i,len(vocabulario)))

  return pares

def main(archivo):
  with open(archivo, 'r', encoding='utf-8') as file:
    texto = file.read()
  tokens = tokenizer(texto)

  archivo_salida = "salida.txt"

  total_tokens = len(tokens)
  vocabulario = len(set(tokens))

  print(f"Tokens:{total_tokens}")
  print(f"Vocabulario:{vocabulario}")

  pares = guardar_pares(tokens)

  with open(archivo_salida, "w", encoding="utf-8") as f:
    for n, v in pares:
      f.write(f"{n} {v}\n")

  print("Archivo exportado:", archivo_salida)
  

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python EJ9.py <texto.txt>")
        sys.exit(1)

    archivo = sys.argv[1]

    main(archivo)

    print("Python Ej9.py")