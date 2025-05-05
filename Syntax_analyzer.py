import json
from pprint import pprint

try:
    from Lexical_Analyzer import lex 
except ImportError:
    raise ImportError("❌ Could not import 'lex' from Lexical_Analyzer.py")

try:
    from anytree import Node, RenderTree
    ANYTREE_AVAILABLE = True
except ImportError:
    ANYTREE_AVAILABLE = False


class SyntaxAnalyzer:
    def __init__(self, tokens):

        self.tokens = list(tokens) 
        self.pos = 0
        print(f"SyntaxAnalyzer initialized with {len(self.tokens)} tokens.")

    def current(self):
        """Returns the current token tuple (type, value) without consuming it."""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None 

    def current_token_info(self):
        """Helper to get current token type and value separately, handling end of stream."""
        current_data = self.current()
        if current_data:

            return current_data[0], current_data[1] 
        return None, None

    def match(self, expected_type=None, expected_value=None):
        """Consumes the current token if it matches expectations, returns the token value."""
        current_data = self.current()
        if current_data:
            token_type, token_value = current_data
            type_match = (expected_type is None or token_type == expected_type)
            value_match = (expected_value is None or token_value == expected_value)

            if type_match and value_match:
                self.pos += 1
                return token_value
        return None

    def expect(self, expected_type=None, expected_value=None):
        """Consumes the current token if it matches, otherwise raises SyntaxError."""
        token_value = self.match(expected_type, expected_value)
        if token_value is None:
            expected_desc = expected_value if expected_value else expected_type
            current_type, current_token = self.current_token_info() # Get type/value order correct
            raise SyntaxError(f"Expected '{expected_desc}' but found '{current_token}' ({current_type}) at position {self.pos}")
        return token_value


    def parse(self):
        """Starts the parsing process."""
        print("\n🚀 Starting Parse...")
        program_body = self.parse_stmt_list()

        if self.pos < len(self.tokens):
             print(f"⚠️ Warning: Parsing finished but tokens remain at pos {self.pos}: {self.tokens[self.pos:]}")
        print("🏁 Parse Finished.")
        return {"type": "Program", "body": program_body}

    def parse_stmt_list(self):
        """Parses a list of statements."""
        stmts = []
        while self.pos < len(self.tokens):
             current_type, current_token = self.current_token_info() 
             if current_token == '}':
                 break
             stmts.append(self.parse_stmt())
        return stmts

    def parse_stmt(self):
        """Parses a single statement."""
        current_type, current_token = self.current_token_info()

        if current_token == 'for' and current_type == 'KEYWORD':
            return self.parse_for_loop()
        elif current_token in ['int', 'float'] and current_type == 'KEYWORD':
            return self.parse_declaration()
        elif current_type == 'ID':

            stmt = self.parse_assignment()
            self.expect('SYMBOL', ';') 
            return stmt
        else:
            raise SyntaxError(f"Unexpected statement starting with token '{current_token}' ({current_type}) at position {self.pos}")


    def parse_declaration(self):
        """Parses 'Type ID ;'"""
        var_type = self.expect('KEYWORD') 
        var_name = self.expect('ID')
        self.expect('SYMBOL', ';')
        return {"type": "Declaration", "var_type": var_type, "var_name": var_name}

    def parse_for_loop(self):
        """Parses 'for ( Assignment ; Condition ; Assignment ) { StmtList }'"""
        self.expect('KEYWORD', 'for')
        self.expect('SYMBOL', '(')
        init = self.parse_assignment()
        self.expect('SYMBOL', ';')
        cond = self.parse_condition()
        self.expect('SYMBOL', ';')
        update = self.parse_assignment()
        self.expect('SYMBOL', ')')
        self.expect('SYMBOL', '{')
        body = self.parse_stmt_list()
        self.expect('SYMBOL', '}')
        return {
            "type": "ForLoop",
            "init": init,
            "condition": cond,
            "update": update,
            "body": body
        }

    def parse_assignment(self):
        """Parses 'ID = Expr'"""
        var_name = self.expect('ID')
        self.expect('ASSIGN', '=') 
        expr = self.parse_expression()
        return {"type": "Assignment", "var": var_name, "expr": expr}

    def parse_condition(self):
        """Parses 'Expr RelOp Expr' """
        left_expr = self.parse_expression()

        op = self.expect('REL_OP') 
        right_expr = self.parse_expression()
        return {"type": "Condition", "left": left_expr, "op": op, "right": right_expr}



    def parse_factor(self):
        """Parses the highest precedence items: Number, Variable, or (Expression)"""
        token_type, token_value = self.current_token_info()

        if self.match('SYMBOL', '('):
            expr = self.parse_expression()
            self.expect('SYMBOL', ')')
            return expr
        elif token_type == 'ID':
            return {"type": "Variable", "name": self.expect('ID')}
        elif token_type == 'NUMBER':
            return {"type": "Number", "value": self.expect('NUMBER')}
        else:
            raise SyntaxError(f"Unexpected token '{token_value}' ({token_type}) at position {self.pos}. Expected number, identifier, or '(' for an expression factor.")

    def parse_term(self):
        """Parses multiplicative expressions: Factor (('*' | '/') Factor)* """
        node = self.parse_factor()
        while True:
            token_type, token_value = self.current_token_info()
            if token_type == 'OP' and token_value in ['*', '/']:
                op = self.expect('OP', token_value)
                right = self.parse_factor()
                node = {"type": "BinaryExpr", "op": op, "left": node, "right": right}
            else:
                break
        return node

    def parse_expression(self):
        """Parses additive expressions: Term (('+' | '-') Term)* """
        node = self.parse_term()
        while True:
            token_type, token_value = self.current_token_info()
            if token_type == 'OP' and token_value in ['+', '-']:
                op = self.expect('OP', token_value)
                right = self.parse_term()
                node = {"type": "BinaryExpr", "op": op, "left": node, "right": right}
            else:
                break
        return node


def pretty_print_ast(ast, indent=0):
    prefix = '  ' * indent
    if isinstance(ast, dict):
        node_type = ast.get('type', 'Dict')
        print(f"{prefix}{node_type}:")
        for key, value in ast.items():
            if key == 'type': continue
            print(f"{prefix}  {key}:")
            pretty_print_ast(value, indent + 2)
    elif isinstance(ast, list):
         print(f"{prefix}List [{len(ast)} items]:")
         for i, item in enumerate(ast):
            pretty_print_ast(item, indent + 1)
    else:
        print(f"{prefix}{str(ast)}")

def visualize_ast(ast, label="AST"):
    pass 

def main():
    input_file = "input.txt"

    print(f"📄 Reading file: {input_file}")
    try:
        with open(input_file, 'r') as f:
            source_code = f.read()
    except FileNotFoundError:
        print(f"❌ Error: Input file '{input_file}' not found.")
        return

    print("\n L E X I N G . . .")
    try:
        tokens = lex(source_code)
        token_list = list(tokens)
        print(f"\n📦 Tokens ({len(token_list)} found):")
        pprint(token_list[:20]) 
        if len(token_list) > 20: print("...")
    except SyntaxError as e:
         print(f"\n❌ Syntax Error during lexical analysis: {e}")
         return
    except Exception as e:
        print(f"❌ Error during tokenization: {e}")
        return

    print("\n P A R S I N G . . .")
    parser = SyntaxAnalyzer(token_list) 

    try:
        ast = parser.parse()


        print("\n🌳 Abstract Syntax Tree (Pretty Print):")
        pretty_print_ast(ast)

        ast_json_file = "AST.json"
        try:
            with open(ast_json_file, "w") as f:
                json.dump(ast, f, indent=4)
            print(f"\n✅ AST saved to {ast_json_file}")
        except IOError as e:
            print(f"❌ Error saving AST to {ast_json_file}: {e}")


    except SyntaxError as e:
        print(f"\n❌ Syntax Error during parsing: {e}")
    except Exception as e:
        print(f"\n❌ An unexpected error occurred during parsing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()