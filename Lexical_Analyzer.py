import re

token_specification = [
    ('COMMENT',        r'//.*'),
    ('NEWLINE',        r'\n'),
    ('SKIP',           r'[ \t]+'),
    ('STRING_LITERAL', r'"(?:\\.|[^"\\])*"'), 
    ('CHAR_LITERAL',   r"'(?:\\.|[^'\\])'"),   
    ('KEYWORD',        r'\b(for|int|float|string|double|char|bool|true|false)\b'), 
    ('ID',             r'\b[a-zA-Z_][a-zA-Z_0-9]*\b'),
    ('NUMBER',         r'\b\d+(\.\d*)?([eE][+-]?\d+)?\b|\.\d+([eE][+-]?\d+)?\b'), 
    ('OP',             r'[+\-*/]'), 
    ('ASSIGN',         r'='),
    ('REL_OP',         r'==|!=|<=|>=|<|>'),
    ('SYMBOL',         r'[{}();]'), 
    ('MISMATCH',       r'.'), 
]

tok_regex = '|'.join(f'(?P<{pair[0]}>{pair[1]})' for pair in token_specification)
get_token = re.compile(tok_regex).match

def lex(code):

    """
    Generates a stream of tokens from the input source code.
    Args:
        code (str): The source code string.
    Yields:
        tuple: A (token_kind, token_value) tuple for each token.
    Raises:
        SyntaxError: If an unexpected character is encountered.
    """

    line_num = 1
    line_start = 0
    pos = 0
    while pos < len(code):
        match_obj = get_token(code, pos) 
        if not match_obj:
            raise SyntaxError(f'Unexpected character: {code[pos]} at line {line_num}, column {pos - line_start + 1}')

        kind = match_obj.lastgroup
        value = match_obj.group()
        pos = match_obj.end()

        if kind == 'NEWLINE':
            line_start = pos
            line_num += 1

        elif kind == 'SKIP' or kind == 'COMMENT':
            continue
        
        elif kind == 'MISMATCH':
            raise SyntaxError(f'Unexpected character: {value} at line {line_num}, column {pos - match_obj.start() - line_start + 1}')
        
        else:
            yield (kind, value)
