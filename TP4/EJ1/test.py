token_especificos = [
    ('EMAIL', r"[a-zA-Z0-9][a-zA-Z0-9._%+\-]*@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"),
    ('URL', r'(?:https?|ftps?)://[^\s<>"\'`]+'), 
    ('ABBREV_MULTI', r"(?:[A-Za-záéíóúüñÁÉÍÓÚÜÑ]{1,4}\.){1,}[A-Za-záéíóúüñÁÉÍÓÚÜÑ]{1,4}\.?"), # Abreviaturas S.A. o U.S.A.
    ('ABBREV', r"[A-Za-záéíóúüñÁÉÍÓÚÜÑ]{2,10}\."), # Abreviaturas Dr., Lic.
    ('PHONE', r"[+\-]?\d[\d.,\-]*(?:%|°)?"), # Telefonos
    ('NUMBER', r'\d+(?:[.,]\d+)*'),
    ('FECHA', r"\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{4}"),
    ('PROPER_NOUN', r"(?:[A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]+)(?:\s+(?!Sra\b|Sr\b|Dr\b)[A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]+)+"), # Nombres propios, con varias palabras con mayúscula
    ('WORD', r"[a-záéíóúüñA-ZÁÉÍÓÚÜÑ]{2,}"),
    ('PUNCT', r'[¡!¿?.,;:]'),
    ('SIGLA', r"[A-ZÁÉÍÓÚÜÑ]{2,}")
]

import re

def tokenizer(texto,stopwords = None, minimo = 2, maximo =float('inf')):
    """
    Tokenizer que pasa todo a minuscula y se queda con letras con acento y ñ (es el mismo que el TP1)

    Args: texto, stopwords, minimo, maximo

    Returns:
        tokens
    """
    tok_regex = '|'.join(f'(?P<{name}>{regex})' for name, regex in token_especificos)
    
    tokens = []
    
    for match in re.finditer(tok_regex, texto):
        kind = match.lastgroup
        value = match.group().strip()

        # Stopwords
        if stopwords and value in stopwords:
            continue
        
        # Minimo y maximo
        if len(value) > maximo or len(value) < minimo:
            continue
        
        tokens.append(value)
    
    return tokens

print(tokenizer("From Wikipedia, the free encyclopedia"))