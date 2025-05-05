import re

token_specification = [
    ('COMMENT',     r'//.*'),
    ('NEWLINE',     r'\n'),
    ('SKIP',        r'[ \t]+'),
    ('STRING_LITERAL', r'"(?:\\.|[^"\\])*"'),
    ('KEYWORD',     r'\b(for|int|float|string)\b'),
    ('ID',          r'\b[a-zA-Z_][a-zA-Z_0-9]*\b'),
    ('NUMBER',      r'\b\d+(\.\d*)?\b|\.\d+\b'),
    ('OP',          r'[+\-*/]'),
    ('ASSIGN',      r'='),
    ('REL_OP',      r'==|!=|<=|>=|<|>'),
    ('SYMBOL',      r'[{}();]'),
    ('MISMATCH',    r'.'),
]

tok_regex = '|'.join(f'(?P<{pair[0]}>{pair[1]})' for pair in token_specification)
get_token = re.compile(tok_regex).match

def lex(code):
    line_num = 1
    line_start = 0
    pos = 0
    while pos < len(code):
        match = get_token(code, pos)
        if not match:
            raise SyntaxError(f'Unexpected character: {code[pos]} at line {line_num}, column {pos - line_start + 1}')

        kind = match.lastgroup
        value = match.group()
        pos = match.end()

        if kind == 'NEWLINE':
            line_start = pos
            line_num += 1
        elif kind == 'SKIP' or kind == 'COMMENT':
            continue
        elif kind == 'MISMATCH':
            raise SyntaxError(f'Unexpected character: {value} at line {line_num}, column {pos - match.start() - line_start + 1}')
        else:
            yield (kind, value)

def main():
    input_file = "input.txt"

    print(f"Running Lexical Analyzer standalone on {input_file}...")
    try:
        with open(input_file, 'r') as file:
            source_code = file.read()
            print("\n--- Source Code ---")
            print(source_code)
            print("-------------------\n")
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        return

    print("Tokens:")
    try:
        token_list = []
        for token in lex(source_code):
            print(f"  {token}")
            token_list.append(token)
        print("\nLexical analysis successful.")
    except SyntaxError as e:
        print(f"\nSyntax Error during lexical analysis: {e}")

if __name__ == "__main__":
    main()
