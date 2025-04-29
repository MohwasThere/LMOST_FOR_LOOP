import re

token_specification = [
    ('KEYWORD', r'\b(for|int|float|double)\b'), #Reseverd Words/ KeyWords
    ('ID',       r'\b[a-zA-Z_][a-zA-Z_0-9]*\b'),
    ('NUM',      r'\b\d+\b'),
    ('OP',       r'[=+<*>/]'),
    ('SYMBOL',   r'[{}();]'),
    ('SKIP',     r'[ \t]+'),   # Skip spaces and tabs
    ('NEWLINE',  r'\n'),
    ('COMMENT',  r'//.*'),     # Single line comments
]

tok_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_specification)
get_token = re.compile(tok_regex).match

def tokenize(code):
    pos = 0
    tokens = []
    while pos < len(code):
        match = get_token(code, pos)
        if match:
            kind = match.lastgroup
            value = match.group()
            if kind not in ['SKIP', 'COMMENT', 'NEWLINE']:
                tokens.append((kind, value))
            pos = match.end()
        else:
            raise SyntaxError(f'Unexpected character: {code[pos]}')
    return tokens

try:
    with open('input.txt', 'r') as file:
        source_code = file.read()
except FileNotFoundError:
    print("File Was Not Found :(")

tokens = tokenize(source_code)

print("Tokens:")
for token in tokens:
    print(token)


#Notes:::
#Should we Handle #include shit wala la2a??