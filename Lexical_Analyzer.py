import re

token_specification = [
    ('KEYWORD',     r'\b(for|int|float)\b'),
    ('ID',          r'\b[a-zA-z_][a-zA-Z_0-9]*\b'),
    ('CONSTANT',    r'\b\d+\b'),
    ('OP',          r'[=+<*-/]'),
    ('EQ',          r'=='),              # ==
    ('NE',          r'!='),              # !=
    ('LE',          r'<='),              # <=
    ('GE',          r'>='),
    ('SYMBOL',      r'[{}();]'),
    ('SKIP',        r'[ \t]+'), # Skip spaces and tabs
    ('NEWLINE',     r'\n'),
    ('COMMENT',     r'//.*'), # Limited to single line comments
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

def analyze(file_path):
    tokens = []

    with open(file_path, 'r') as file:
        lines = file.readlines()

    for line in lines:
        line = line.strip()

        # Add your logic here to tokenize each line
        # Here's a dummy implementation for example:
        words = line.replace('(', ' ( ').replace(')', ' ) ').replace('{', ' { ')\
                    .replace('}', ' } ').replace(';', ' ; ').replace('=', ' = ')\
                    .replace('+', ' + ').replace('-', ' - ').replace('*', ' * ')\
                    .replace('/', ' / ').replace('<', ' < ').split()

        for word in words:
            if word in ['int', 'float', 'for']:
                tokens.append((word, 'KEYWORD'))
            elif word in ['(', ')', '{', '}', ';']:
                tokens.append((word, 'SYMBOL'))
            elif word in ['=', '+', '-', '*', '/', '<', '>', '==', '<=', '>=', '!=']:
                tokens.append((word, 'OPERATOR'))
            elif word.isdigit():
                tokens.append((word, 'NUMBER'))
            elif word.replace('.', '', 1).isdigit():
                tokens.append((word, 'NUMBER'))
            elif word.isidentifier():
                tokens.append((word, 'IDENTIFIER'))
            else:
                tokens.append((word, 'UNKNOWN'))

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