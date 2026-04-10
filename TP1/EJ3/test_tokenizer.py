import re

token_especificos = [
    ('EMAIL', r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]+'),
    ('URL', r'https?://[^\s]+|www\.[^\s]+'), 
    ('ABBREV_MULTI', r'(?:[A-Za-z]\.){2,}'), # Abreviaturas S.A. o U.S.A.
    ('ABBREV', r'\b[A-Z][a-z]{1,5}\.'), # Abreviaturas Dr., Lic.
    ('PHONE', r'\+?\d[\d\s\-]{6,}\d'), # Telefonos
    ('NUMBER', r'\d+(?:[.,]\d+)*'),
    ('PROPER_NOUN', r'(?:\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+|$)){2,}'), # Nombres propios, con varias palabras con mayúscula
    ('WORD', r'\b[a-záéíóúñ]+\b'),
    ('PUNCT', r'[¡!¿?.,;:]'),
]

def nuevo_tokenizer(texto):
    tok_regex = '|'.join(f'(?P<{name}>{regex})' for name, regex in token_especificos)
    
    tokens = []
    
    for match in re.finditer(tok_regex, texto):
        kind = match.lastgroup
        value = match.group().strip()
        
        tokens.append((kind, value))
    
    return tokens

text = """
El Ing. Juan Pérez trabaja en S.A. Tech.
Podés escribirle a juan.perez@gmail.com o visitar https://empresa.com.
Vive en Villa Carlos Paz y su teléfono es +54 11 1234-5678.
Ganó 123,456.78 pesos.
"""

tokens = nuevo_tokenizer(text)

for t in tokens:
    print(t)