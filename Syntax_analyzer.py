import json
from pprint import pprint

# Try importing your lexical analyzer
try:
    from Lexical_Analyzer import analyze
except ImportError:
    raise ImportError("❌ Could not import 'analyze' from Lexical_Analyzer.py")

# Optional tree rendering
try:
    from anytree import Node, RenderTree
    ANYTREE_AVAILABLE = True
except ImportError:
    ANYTREE_AVAILABLE = False

class SyntaxAnalyzer:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def match(self, expected_type=None, expected_value=None):
        if self.pos < len(self.tokens):
            token, type_ = self.tokens[self.pos]
            if (expected_type is None or type_ == expected_type) and (expected_value is None or token == expected_value):
                self.pos += 1
                return token
        return None

    def expect(self, expected_type=None, expected_value=None):
        token = self.match(expected_type, expected_value)
        if token is None:
            raise SyntaxError(f"Expected {expected_value or expected_type} at position {self.pos}")
        return token

    def parse(self):
        return {"type": "Program", "body": self.parse_stmt_list()}

    def parse_stmt_list(self):
        stmts = []
        while self.pos < len(self.tokens) and self.current()[0] != '}':
            stmts.append(self.parse_stmt())
        return stmts

    def parse_stmt(self):
        token, type_ = self.current()
        if token == 'for':
            return self.parse_for_loop()
        elif token in ['int', 'float']:
            return self.parse_declaration()
        else:
            stmt = self.parse_assignment()
            self.expect('SYMBOL', ';')
            return stmt

    def parse_declaration(self):
        var_type = self.expect('KEYWORD')
        var_name = self.expect('IDENTIFIER')
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
        var = self.expect('IDENTIFIER')
        self.expect('OPERATOR', '=')
        expr = self.parse_expression()
        return {"type": "Assignment", "var": var, "expr": expr}

    def parse_expression(self):
        left = self.parse_term()
        while True:
            op = self.match('OPERATOR')
            if op and op in ['+', '-', '*', '/']:
                right = self.parse_term()
                left = {"type": "BinaryExpr", "op": op, "left": left, "right": right}
            else:
                break
        return left

    def parse_term(self):
        token, type_ = self.current()
        if token == '(':
            self.expect('SYMBOL', '(')
            expr = self.parse_expression()
            self.expect('SYMBOL', ')')
            return expr
        elif type_ == 'IDENTIFIER':
            return {"type": "Variable", "name": self.expect('IDENTIFIER')}
        elif type_ == 'NUMBER':
            return {"type": "Number", "value": self.expect('NUMBER')}
        else:
            raise SyntaxError(f"Unexpected token '{token}' at position {self.pos}")

    def parse_condition(self):
        left = self.expect('IDENTIFIER')
        op = self.expect('OPERATOR')
        right = self.parse_expression()
        return {"type": "Condition", "left": left, "op": op, "right": right}


# Pretty Print AST to Terminal
def pretty_print_ast(ast, indent=0):
    if isinstance(ast, dict):
        for key, value in ast.items():
            print('  ' * indent + f"{key}:")
            pretty_print_ast(value, indent + 1)
    elif isinstance(ast, list):
        for i, item in enumerate(ast):
            print('  ' * indent + f"[{i}]")
            pretty_print_ast(item, indent + 1)
    else:
        print('  ' * indent + str(ast))


# Optional: Visualize AST Tree (requires anytree)
def visualize_ast(ast, label="AST"):
    if not ANYTREE_AVAILABLE:
        print("\n(Tree visualization skipped: `anytree` not installed)")
        return

    def build_tree(ast, label="root"):
        if isinstance(ast, dict):
            root = Node(label)
            for k, v in ast.items():
                child = build_tree(v, k)
                child.parent = root
            return root
        elif isinstance(ast, list):
            root = Node(label)
            for i, item in enumerate(ast):
                child = build_tree(item, f"[{i}]")
                child.parent = root
            return root
        else:
            return Node(f"{label}: {ast}")

    tree_root = build_tree(ast, label)
    print("\n📊 AST Tree:")
    for pre, _, node in RenderTree(tree_root):
        print(f"{pre}{node.name}")


# Main runner
def main():
    input_file = "input.txt"

    print(f"📄 Reading file: {input_file}")
    tokens = analyze(input_file)
    print("\n📦 Tokens:")
    pprint(tokens)

    parser = SyntaxAnalyzer(tokens)
    try:
        ast = parser.parse()

        print("\n🌳 Abstract Syntax Tree (Pretty Print):")
        pretty_print_ast(ast)

        # Save to JSON
        with open("AST.json", "w") as f:
            json.dump(ast, f, indent=4)
        print("\n✅ AST saved to syntax_tree.json")

        # Optional tree view
        visualize_ast(ast)

    except SyntaxError as e:
        print(f"\n❌ Syntax Error: {e}")


if __name__ == "__main__":
    main()