import json
from Lexical_Analyzer import analyze
from Syntax_analyzer import SyntaxAnalyzer, pretty_print_ast, pprint

class SemanticAnalyzer:
    def __init__(self, ast):
        self.ast = ast
        self.symbol_table = {}
        self.errors = []
        self.declared_vars = set()

    def analyze(self):
        print("\n🔬 Starting Semantic Analysis...")
        self.visit(self.ast)
        print("🔬 Semantic Analysis Finished.")
        return self.symbol_table, self.errors

    def visit(self, node):
        if isinstance(node, list):
            for item in node:
                self.visit(item)
        elif isinstance(node, dict) and 'type' in node:
            method_name = f'visit_{node["type"]}'
            visitor = getattr(self, method_name, self.generic_visit)
            visitor(node)
        elif isinstance(node, (str, int, float)):
            pass
        else:
            print(f"🔍 Skipping unknown node structure: {type(node)} {node}")

    def generic_visit(self, node):
        print(f"🔍 Visiting generic node: {node.get('type', 'Unknown')}")
        if isinstance(node, dict):
            for key, value in node.items():
                if isinstance(value, (dict, list)):
                    self.visit(value)

    def visit_Declaration(self, node):
        var_name = node.get("var_name")
        var_type = node.get("var_type")
        print(f"Visiting Declaration: var_name='{var_name}', var_type='{var_type}'")

        if not var_name or not var_type:
            self.errors.append(f"Error: Invalid declaration node structure: {node}")
            return

        if var_name in self.declared_vars:
            self.errors.append(f"Error: Variable '{var_name}' is already declared.")
        else:
            self.declared_vars.add(var_name)
            self.symbol_table[var_name] = {"type": var_type, "initialized": False}
            print(f"  -> Added '{var_name}' (type: {var_type}) to symbol table.")

    def visit_Assignment(self, node):
        var_name = node.get("var")
        expression_node = node.get("expr")
        print(f"Visiting Assignment: var='{var_name}'")

        if not var_name or expression_node is None:
            self.errors.append(f"Error: Invalid assignment node structure: {node}")
            return

        if var_name not in self.symbol_table:
            self.errors.append(f"Error: Variable '{var_name}' is not declared before assignment.")
            return

        expr_type = self.get_expression_type(expression_node)
        print(f"  -> Expression type determined as: {expr_type}")

        if expr_type != "Unknown":
            declared_type = self.symbol_table[var_name]["type"]

            if declared_type != expr_type:
                self.errors.append(f"Error: Type mismatch in assignment to '{var_name}'. Expected '{declared_type}', got '{expr_type}'.")
            else:
                self.symbol_table[var_name]["initialized"] = True
                print(f"  -> Marked '{var_name}' as initialized.")
        else:
            print(f"  -> Could not determine expression type, skipping assignment check for '{var_name}'.")

    def visit_ForLoop(self, node):
        print("Visiting ForLoop")
        if "init" in node:
            self.visit(node["init"])
        if "condition" in node:
            self.visit(node["condition"])
        if "update" in node:
            self.visit(node["update"])
        if "body" in node:
            self.visit(node["body"])

    def visit_Condition(self, node):
        left_node = node.get("left")
        right_node = node.get("right")
        op = node.get("op")
        print(f"Visiting Condition: op='{op}'")

        if left_node is None or right_node is None or op is None:
            self.errors.append(f"Error: Invalid condition node structure: {node}")
            return

        left_type = self.get_expression_type(left_node)
        right_type = self.get_expression_type(right_node)
        print(f"  -> Condition types: Left='{left_type}', Right='{right_type}'")

        if left_type != "Unknown" and right_type != "Unknown" and left_type != right_type:
            self.errors.append(f"Error: Incompatible types in condition ({op}). Left: '{left_type}', Right: '{right_type}'.")

        if op not in ['<', '>', '==', '!=', '<=', '>=']:
            self.errors.append(f"Error: Unsupported operator '{op}' used in condition.")

    def visit_BinaryExpr(self, node):
        print(f"Visiting BinaryExpr: op='{node.get('op')}'")
        self.visit(node.get("left"))
        self.visit(node.get("right"))

    def visit_Variable(self, node):
        var_name = node.get("name")
        print(f"Visiting Variable (usage): name='{var_name}'")
        if var_name not in self.symbol_table:
            self.errors.append(f"Error: Variable '{var_name}' used before declaration.")

    def visit_Number(self, node):
        print(f"Visiting Number: value='{node.get('value')}'")
        pass

    def get_expression_type(self, expr_node):
        if not isinstance(expr_node, dict) or 'type' not in expr_node:
            if isinstance(expr_node, (int, float)): return "int"
            if isinstance(expr_node, str):
                return self.get_variable_type(expr_node)
            print(f"⚠️ Cannot determine type for non-standard expression node: {expr_node}")
            return "Unknown"

        node_type = expr_node["type"]

        if node_type == "Number":
            return "int"
        elif node_type == "Variable":
            var_name = expr_node.get("name")
            self.visit_Variable(expr_node)
            return self.get_variable_type(var_name)
        elif node_type == "BinaryExpr":
            left_type = self.get_expression_type(expr_node.get("left"))
            right_type = self.get_expression_type(expr_node.get("right"))
            op = expr_node.get("op")

            if left_type == "Unknown" or right_type == "Unknown":
                return "Unknown"

            if left_type != right_type:
                self.errors.append(f"Error: Type mismatch in binary expression ('{op}'). Left: '{left_type}', Right: '{right_type}'.")
                return "Unknown"

            return left_type
        else:
            print(f"⚠️ Unknown expression node type: {node_type}")
            self.generic_visit(expr_node)
            return "Unknown"

    def get_variable_type(self, var_name):
        if var_name in self.symbol_table:
            return self.symbol_table[var_name]["type"]
        else:
            return "Unknown"

# Main function to integrate everything
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

        # Semantic analysis
        semantic_analyzer = SemanticAnalyzer(ast)
        symbol_table, errors = semantic_analyzer.analyze()

        if errors:
            print("\n❌ Semantic Errors Found:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("\n✅ No Semantic Errors Found.")

        print("\n💼 Final Symbol Table:")
        pprint(symbol_table)

        # Save Symbol Table to a JSON file
        with open("symbol_table.json", "w") as f:
            json.dump(symbol_table, f, indent=4)
        print("\n✅ Symbol Table saved to symbol_table.json")

        # Save AST to JSON
        with open("AST.json", "w") as f:
            json.dump(ast, f, indent=4)
        print("\n✅ AST saved to AST.json")

    except Exception as e:
        print(f"\n❌ An Error Occurred: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
