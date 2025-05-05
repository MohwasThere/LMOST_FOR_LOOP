import json
from pprint import pprint

try:
    from Lexical_Analyzer import lex 
except ImportError:
    raise ImportError("❌ Could not import 'lex' from Lexical_Analyzer.py")


try:
    from Syntax_analyzer import SyntaxAnalyzer, pretty_print_ast 
except ImportError:
    raise ImportError("❌ Could not import 'SyntaxAnalyzer' from Syntax_analyzer.py")



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
            print(f"🔍 Skipping unknown node structure in Semantic: {type(node)} {node}")

    def generic_visit(self, node):

        if isinstance(node, dict):
            for key, value in node.items():
                if isinstance(value, (dict, list)):
                    self.visit(value)

    def visit_Program(self, node):
        self.visit(node.get('body', [])) 


    def visit_Declaration(self, node):
        var_name = node.get("var_name")
        var_type = node.get("var_type")

        if not var_name or not var_type:
            self.errors.append(f"Error: Invalid declaration node structure: {node}")
            return

        if var_name in self.declared_vars:
            self.errors.append(f"Error: Variable '{var_name}' is already declared in this scope.")
        else:
            self.declared_vars.add(var_name)
            self.symbol_table[var_name] = {"type": var_type, "initialized": False}

    def visit_Assignment(self, node):
        var_name = node.get("var")
        expression_node = node.get("expr")

        if not var_name or expression_node is None:
            self.errors.append(f"Error: Invalid assignment node structure: {node}")
            return


        if var_name not in self.symbol_table:
            self.errors.append(f"Error: Variable '{var_name}' is not declared before assignment.")
            self.visit(expression_node)
            return 


        expr_type = self.get_expression_type(expression_node)


        if expr_type != "Unknown": 
            declared_type = self.symbol_table[var_name]["type"]


            if declared_type != expr_type:

                 if not (declared_type == 'float' and expr_type == 'int'):
                    self.errors.append(f"Error: Type mismatch in assignment to '{var_name}'. Expected '{declared_type}', got '{expr_type}'.")

            self.symbol_table[var_name]["initialized"] = True

        else:

            self.symbol_table[var_name]["initialized"] = True



    def visit_ForLoop(self, node):
        if "init" in node: self.visit(node["init"])
        if "condition" in node: self.visit(node["condition"])
        if "update" in node: self.visit(node["update"])
        if "body" in node: self.visit(node["body"]) 

    def visit_Condition(self, node):
        left_node = node.get("left")
        right_node = node.get("right")
        op = node.get("op")


        if left_node is None or right_node is None or op is None:
            self.errors.append(f"Error: Invalid condition node structure: {node}")
            return


        left_type = self.get_expression_type(left_node)
        right_type = self.get_expression_type(right_node)


        if left_type != "Unknown" and right_type != "Unknown":
             allowed_types = {'int', 'float'}
             if not (left_type in allowed_types and right_type in allowed_types):
                 self.errors.append(f"Error: Incompatible types in condition ({op}). Cannot compare '{left_type}' and '{right_type}'.")


    def visit_BinaryExpr(self, node):

        left_type = self.get_expression_type(node.get("left"))
        right_type = self.get_expression_type(node.get("right"))
        op = node.get("op")

        # Check type compatibility for the operation
        if left_type != "Unknown" and right_type != "Unknown":
            allowed_types = {'int', 'float'}
            if not (left_type in allowed_types and right_type in allowed_types):
                self.errors.append(f"Error: Incompatible types for operator '{op}'. Cannot use '{left_type}' and '{right_type}'.")



    def visit_Variable(self, node):
        var_name = node.get("name")

        if var_name not in self.symbol_table:
            self.errors.append(f"Error: Variable '{var_name}' used before declaration.")


    def visit_Number(self, node):

        pass 

    def get_expression_type(self, expr_node):
        """Recursively determines the type of an expression node."""
        node_type = None
        if isinstance(expr_node, dict) and 'type' in expr_node:
             node_type = expr_node["type"]
        elif isinstance(expr_node, int): return "int"
        elif isinstance(expr_node, float): return "float"


        if node_type == "Number":
            value_str = str(expr_node.get('value', ''))
            if '.' in value_str:
                return "float"
            else:
                return "int"
        elif node_type == "Variable":
            var_name = expr_node.get("name")
            self.visit_Variable(expr_node) 
            return self.get_variable_type(var_name) 
        elif node_type == "BinaryExpr":
            left_type = self.get_expression_type(expr_node.get("left"))
            right_type = self.get_expression_type(expr_node.get("right"))


            if left_type == "Unknown" or right_type == "Unknown":
                return "Unknown"
            elif left_type == "float" or right_type == "float":
                return "float" 
            else:
                return "int" 
        else:

            return "Unknown"

    def get_variable_type(self, var_name):
        """Looks up variable type in the symbol table."""
        if var_name in self.symbol_table:
            return self.symbol_table[var_name]["type"]
        else:
            return "Unknown"


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
        tokens = list(lex(source_code)) 
        print(f"\n📦 Tokens ({len(tokens)} found):")

    except Exception as e:
        print(f"❌ Error during Lexical Analysis: {e}")
        return

    print("\n P A R S I N G . . .")
    parser = SyntaxAnalyzer(tokens)
    try:
        ast = parser.parse()
    except Exception as e:
        print(f"❌ Error during Syntax Analysis: {e}")
        return

    print("\n S E M A N T I C   A N A L Y S I S . . .")
    semantic_analyzer = SemanticAnalyzer(ast)
    try:
        symbol_table, errors = semantic_analyzer.analyze()

        sym_table_file = "symbol_table.json"
        try:
            with open(sym_table_file, "w") as f:
                json.dump(symbol_table, f, indent=4)
            print(f"\n✅ Symbol Table saved to {sym_table_file}")
        except IOError as e:
            print(f"❌ Error saving Symbol Table to {sym_table_file}: {e}")

        ast_file = "AST.json"
        try:
            with open(ast_file, "w") as f:
                json.dump(ast, f, indent=4)
            print(f"✅ AST saved to {ast_file}")
        except IOError as e:
             print(f"❌ Error saving AST to {ast_file}: {e}")


        if errors:
            print("\n❌ Semantic Errors Found:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("\n✅ No Semantic Errors Found.")

        print("\n💼 Final Symbol Table:")
        pprint(symbol_table)

    except Exception as e:
        print(f"\n❌ An unexpected error occurred during Semantic Analysis: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()