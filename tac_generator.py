import json
from pprint import pprint
import sys
import re

try:
    from Lexical_Analyzer import lex
except ImportError:
    raise ImportError("Could not import 'lex' from Lexical_Analyzer.py")
try:
    from Syntax_analyzer import SyntaxAnalyzer
except ImportError:
    raise ImportError("Could not import 'SyntaxAnalyzer' from Syntax_analyzer.py")
try:
    from Semantic_analyzer import SemanticAnalyzer
except ImportError:
    raise ImportError("Could not import 'SemanticAnalyzer' from Semantic_analyzer.py")

class TACGenerator:
    def __init__(self):
        self.temp_count = 0
        self.label_count = 0
        self.tac_code = []
        self.string_literals = {}
        self.string_label_count = 0

    def new_temp(self):
        temp_name = f"t{self.temp_count}"
        self.temp_count += 1
        return temp_name

    def new_label(self):
        label_name = f"L{self.label_count}"
        self.label_count += 1
        return label_name

    def new_string_label(self, string_value):
        actual_string = string_value[1:-1]

        if actual_string not in self.string_literals:
            label = f"_str{self.string_label_count}"
            self.string_literals[actual_string] = label
            self.string_label_count += 1
            return label
        else:
            return self.string_literals[actual_string]

    def add_instruction(self, op, arg1=None, arg2=None, result=None):
        instruction = {'op': op, 'arg1': arg1, 'arg2': arg2, 'result': result}
        self.tac_code.append(instruction)

    def generate(self, node):
        print("\nStarting TAC Generation...")
        self.visit(node)
        print("TAC Generation Finished.")
        return self.tac_code, self.string_literals

    def visit(self, node):
        if isinstance(node, list):
            results = []
            for item in node:
                results.append(self.visit(item))
            return [res for res in results if res is not None]
        elif isinstance(node, dict) and 'type' in node:
            method_name = f'visit_{node["type"]}'
            visitor = getattr(self, method_name, self.generic_visit)
            return visitor(node)
        elif isinstance(node, (str, int, float)):
            return node
        elif node is None:
            return None
        else:
            return None

    def generic_visit(self, node):
        result = None
        if isinstance(node, dict):
            for key, value in node.items():
                if isinstance(value, (dict, list)):
                    self.visit(value)
        return result

    def visit_Program(self, node):
        self.visit(node.get('body', []))
        return None

    def visit_Declaration(self, node):
        return None

    def visit_Assignment(self, node):
        var_name = node.get('var')
        expr_result = self.visit(node.get('expr'))
        if expr_result is not None:
            self.add_instruction('ASSIGN', expr_result, None, var_name)
        return None

    def visit_BinaryExpr(self, node):
        op = node.get('op')
        left_result = self.visit(node.get('left'))
        right_result = self.visit(node.get('right'))

        if left_result is None or right_result is None:
             print(f"Warning: Operands for '{op}' were None. Skipping instruction.")
             return self.new_temp()

        result_temp = self.new_temp()

        if op == '+':
            if isinstance(left_result, str) and left_result.startswith('_str') or \
               isinstance(right_result, str) and right_result.startswith('_str'):
                 self.add_instruction('CONCAT', left_result, right_result, result_temp)
            else:
                 self.add_instruction('ADD', left_result, right_result, result_temp)
        elif op == '-':
            self.add_instruction('SUB', left_result, right_result, result_temp)
        elif op == '*':
            self.add_instruction('MUL', left_result, right_result, result_temp)
        elif op == '/':
            self.add_instruction('DIV', left_result, right_result, result_temp)
        else:
            print(f"Warning: Unsupported binary operator '{op}' skipped in TAC gen.")
            return result_temp

        return result_temp

    def visit_UnaryExpr(self, node):
        op = node.get("op")
        operand_result = self.visit(node.get("operand"))

        if operand_result is None:
            print(f"Warning: Operand for unary '{op}' was None. Skipping instruction.")
            return self.new_temp()

        if op == '-':
            result_temp = self.new_temp()
            self.add_instruction('UMINUS', operand_result, None, result_temp)
            return result_temp
        else:
            print(f"Warning: Unsupported unary operator '{op}' skipped in TAC gen.")
            return operand_result

    def visit_Variable(self, node):
        return node.get('name')

    def visit_Number(self, node):
        return node.get('value')

    def visit_StringLiteral(self, node):
        string_value = node.get('value')
        string_label = self.new_string_label(string_value)
        return string_label

    def visit_Condition(self, node):
        left_result = self.visit(node.get('left'))
        right_result = self.visit(node.get('right'))
        return (left_result, node.get('op'), right_result)

    def visit_ForLoop(self, node):
        self.visit(node.get('init'))
        start_loop_label = self.new_label()
        self.add_instruction('LABEL', start_loop_label)
        cond_result = self.visit(node.get('condition'))
        body_label = self.new_label()
        after_loop_label = self.new_label()

        if cond_result:
            cond_left, cond_op, cond_right = cond_result
            self.add_instruction(f'IF_{cond_op}', cond_left, cond_right, body_label)
            self.add_instruction('GOTO', after_loop_label)
        else:
             print("Warning: Failed to evaluate condition in ForLoop. Generating unconditional jump past loop.")
             self.add_instruction('GOTO', after_loop_label)

        self.add_instruction('LABEL', body_label)
        self.visit(node.get('body'))
        self.visit(node.get('update'))
        self.add_instruction('GOTO', start_loop_label)
        self.add_instruction('LABEL', after_loop_label)
        return None

def main():
    input_file = "input.txt"
    ast_file = "AST.json"
    sym_table_file = "symbol_table.json"
    tac_output_file = "tac_code.txt"

    print(f"--- COMPILER PIPELINE ---")
    print(f"Reading file: {input_file}")
    try:
        with open(input_file, 'r') as f:
            source_code = f.read()
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        sys.exit(1)

    print("\n L E X I N G . . .")
    try:
        tokens = list(lex(source_code))
        print(f"Lexing successful ({len(tokens)} tokens found).")
    except SyntaxError as e:
         print(f"\nSyntax Error during lexical analysis: {e}")
         sys.exit(1)
    except Exception as e:
        print(f"Unexpected Error during Lexical Analysis: {e}")
        sys.exit(1)

    print("\n P A R S I N G . . .")
    parser = SyntaxAnalyzer(tokens)
    try:
        ast = parser.parse()
        print("Parsing successful.")
        try:
            with open(ast_file, "w") as f: json.dump(ast, f, indent=4)
        except IOError: pass
    except SyntaxError as e:
        print(f"\nSyntax Error during parsing: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected Error during Parsing: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)

    print("\n S E M A N T I C   A N A L Y S I S . . .")
    semantic_analyzer = SemanticAnalyzer(ast)
    try:
        symbol_table, errors = semantic_analyzer.analyze()
        try:
            with open(sym_table_file, "w") as f: json.dump(symbol_table, f, indent=4)
        except IOError: pass

        if errors:
            print("\nSemantic Errors Found:")
            for error in errors:
                print(f"  - {error}")
            print("Aborting before TAC generation due to semantic errors.")
            sys.exit(1)
        else:
            print("\nNo Semantic Errors Found.")

    except Exception as e:
        print(f"\nAn unexpected error occurred during Semantic Analysis: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)

    print("\n T A C   G E N E R A T I O N . . .")
    generator = TACGenerator()
    try:
        tac_instructions, string_data = generator.generate(ast)
        print("TAC generation successful.")

        print("\nGenerated TAC Instructions:")
        output_lines = []
        output_lines.append(".code")
        for i, instruction in enumerate(tac_instructions):
            op = instruction['op']
            arg1 = instruction.get('arg1', '')
            arg2 = instruction.get('arg2', '')
            result = instruction.get('result', '')
            arg1_str = str(arg1) if arg1 is not None else ''
            arg2_str = str(arg2) if arg2 is not None else ''
            result_str = str(result) if result is not None else ''

            line = ""
            if op.startswith("IF_"):
                 op_suffix = op.split('_')[1]
                 line = f"{i:03d}:  if {arg1_str} {op_suffix} {arg2_str} goto {result_str}"
            elif op == "GOTO":
                line = f"{i:03d}:  goto {arg1_str}"
            elif op == "LABEL":
                line = f"{i:03d}: {arg1_str}:"
            elif op == "ASSIGN":
                line = f"{i:03d}:  {result_str} = {arg1_str}"
            elif op == "UMINUS":
                 line = f"{i:03d}:  {result_str} = - {arg1_str}"
            elif op in ['ADD', 'SUB', 'MUL', 'DIV', 'CONCAT']:
                op_symbol = {'ADD':'+', 'SUB':'-', 'MUL':'*', 'DIV':'/', 'CONCAT': '+'}.get(op, op)
                line = f"{i:03d}:  {result_str} = {arg1_str} {op_symbol} {arg2_str}"
            else:
                line = f"{i:03d}:  {op} {arg1_str} {arg2_str} {result_str}"
            print(line)
            output_lines.append(line.strip())

        if string_data:
            print("\nString Literal Data:")
            output_lines.append(".data")
            for string_val, label in string_data.items():
                escaped_string = string_val.replace('\\', '\\\\').replace('"', '\\"')
                line = f"{label}: .asciiz \"{escaped_string}\""
                print(line)
                output_lines.append(line)

        try:
            with open(tac_output_file, 'w') as f:
                 f.write('\n'.join(output_lines))
            print(f"\nTAC (including data section) saved to {tac_output_file}")
        except IOError:
            print(f"Error: Could not write TAC to {tac_output_file}")

    except Exception as e:
        print(f"\nAn unexpected error occurred during TAC Generation: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)

    print("\n--- COMPILER PIPELINE FINISHED ---")

if __name__ == "__main__":
    main()
