import json
from pprint import pprint

try:
    from Lexical_Analyzer import lex
except ImportError:
    raise ImportError("Could not import 'lex' from Lexical_Analyzer.py")

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
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def current_token_info(self):
        current_data = self.current()
        if current_data:
            return current_data[0], current_data[1]
        return None, None

    def match(self, expected_type=None, expected_value=None):
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
        token_value = self.match(expected_type, expected_value)
        if token_value is None:
            expected_desc = expected_value if expected_value else expected_type
            current_type, current_token = self.current_token_info()
            raise SyntaxError(f"Expected '{expected_desc}' but found '{current_token}' ({current_type}) at position {self.pos}")
        return token_value

    def parse(self):
        print("\nStarting Parse...")
        program_body = self.parse_stmt_list()
        if self.pos < len(self.tokens):
             print(f"Warning: Parsing finished but tokens remain at pos {self.pos}: {self.tokens[self.pos:]}")
        print("Parse Finished.")
        return {"type": "Program", "body": program_body}

    def parse_stmt_list(self):
        stmts = []
        while self.pos < len(self.tokens):
             current_type, current_token = self.current_token_info()
             if current_token == '}':
                 break
             stmts.append(self.parse_stmt())
        return stmts

    def parse_stmt(self):
        current_type, current_token = self.current_token_info()

        if current_token == 'for' and current_type == 'KEYWORD':
            return self.parse_for_loop()
        elif current_token in ['int', 'float', 'string'] and current_type == 'KEYWORD':
            return self.parse_declaration()
        elif current_type == 'ID':
            stmt = self.parse_assignment()
            self.expect('SYMBOL', ';')
            return stmt
        else:
            raise SyntaxError(f"Unexpected statement starting with token '{current_token}' ({current_type}) at position {self.pos}")

    def parse_declaration(self):
        var_type = self.expect('KEYWORD')
        if var_type not in ['int', 'float', 'string']:
             raise SyntaxError(f"Expected type (int, float, string) but found '{var_type}' at position {self.pos-1}")
        var_name = self.expect('ID')
        self.expect('SYMBOL', ';')
        return {"type": "Declaration", "var_type": var_type, "var_name": var_name}

    def parse_for_loop(self):
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
        var_name = self.expect('ID')
        self.expect('ASSIGN', '=')
        expr = self.parse_expression()
        return {"type": "Assignment", "var": var_name, "expr": expr}

    def parse_condition(self):
        left_expr = self.parse_expression()
        op = self.expect('REL_OP')
        right_expr = self.parse_expression()
        return {"type": "Condition", "left": left_expr, "op": op, "right": right_expr}

    def parse_factor(self):
        token_type, token_value = self.current_token_info()

        if self.match('SYMBOL', '('):
            expr = self.parse_expression()
            self.expect('SYMBOL', ')')
            return expr
        elif token_type == 'ID':
            return {"type": "Variable", "name": self.expect('ID')}
        elif token_type == 'NUMBER':
            return {"type": "Number", "value": self.expect('NUMBER')}
        elif token_type == 'STRING_LITERAL':
            return {"type": "StringLiteral", "value": self.expect('STRING_LITERAL')}
        else:
            raise SyntaxError(f"Unexpected token '{token_value}' ({token_type}) at position {self.pos}. Expected number, string, identifier, or '(' for an expression factor.")

    def parse_term(self):
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
            print(f"{prefix}  {key}:", end="")
            if isinstance(value, (dict, list)):
                print()
                pretty_print_ast(value, indent + 2)
            else:
                print(f" {repr(value)}")
    elif isinstance(ast, list):
         print(f"{prefix}List [{len(ast)} items]:")
         for i, item in enumerate(ast):
            pretty_print_ast(item, indent + 1)
    else:
        print(f"{prefix}{repr(ast)}")

def visualize_ast(ast, label="AST"):
    if not ANYTREE_AVAILABLE:
        print("\nNote: 'anytree' library not found. Skipping tree visualization.")
        return

    def build_tree(node_data, parent=None):
        if isinstance(node_data, dict):
            node_type = node_data.get('type', 'Dict')
            label_parts = [node_type]
            for key, value in node_data.items():
                if key != 'type' and not isinstance(value, (dict, list)):
                    label_parts.append(f"{key}={repr(value)}")
            node_label = "\n".join(label_parts)

            current_node = Node(node_label, parent=parent)
            for key, value in node_data.items():
                if key != 'type' and isinstance(value, (dict, list)):
                    build_tree(value, parent=current_node)
        elif isinstance(node_data, list):
            list_node = Node(f"List[{len(node_data)}]", parent=parent)
            for i, item in enumerate(node_data):
                build_tree(item, parent=list_node)
        else:
            Node(repr(node_data), parent=parent)

    root_node = Node(label)
    build_tree(ast, parent=root_node)

    print("\nAbstract Syntax Tree (Visualization):")
    for pre, _, node in RenderTree(root_node):
        print(f"{pre}{node.name}")

def main():
    input_file = "input.txt"

    print(f"Reading file: {input_file}")
    try:
        with open(input_file, 'r') as f:
            source_code = f.read()
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        return

    print("\n L E X I N G . . .")
    try:
        tokens = lex(source_code)
        token_list = list(tokens)
        print(f"\nTokens ({len(token_list)} found):")

    except SyntaxError as e:
         print(f"\nSyntax Error during lexical analysis: {e}")
         return
    except Exception as e:
        print(f"Error during tokenization: {e}")
        return

    print("\n P A R S I N G . . .")
    parser = SyntaxAnalyzer(token_list)

    try:
        ast = parser.parse()

        print("\nAbstract Syntax Tree (Pretty Print):")
        pretty_print_ast(ast)

        ast_json_file = "AST.json"
        try:
            with open(ast_json_file, "w") as f:
                json.dump(ast, f, indent=4)
            print(f"\nAST saved to {ast_json_file}")
        except IOError as e:
            print(f"Error saving AST to {ast_json_file}: {e}")


    except SyntaxError as e:
        print(f"\nSyntax Error during parsing: {e}")
    except Exception as e:
        print(f"\nAn unexpected error occurred during parsing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
