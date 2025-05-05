import json
import sys 


try:
    from Lexical_Analyzer import lex
except ImportError:
    raise ImportError("❌ Could not import 'lex' from Lexical_Analyzer.py")
try:
    from Syntax_analyzer import SyntaxAnalyzer
except ImportError:
    raise ImportError("❌ Could not import 'SyntaxAnalyzer' from Syntax_analyzer.py")
try:
    from Semantic_analyzer import SemanticAnalyzer
except ImportError:
    raise ImportError("❌ Could not import 'SemanticAnalyzer' from Semantic_analyzer.py")



class TACGenerator:
    def __init__(self):
        self.temp_count = 0
        self.label_count = 0
        self.tac_code = [] 

    def new_temp(self):
        temp_name = f"t{self.temp_count}"
        self.temp_count += 1
        return temp_name

    def new_label(self):
        label_name = f"L{self.label_count}"
        self.label_count += 1
        return label_name

    def add_instruction(self, op, arg1=None, arg2=None, result=None):
        instruction = {'op': op, 'arg1': arg1, 'arg2': arg2, 'result': result}
        self.tac_code.append(instruction)


    def generate(self, node):
        print("\n⚙️ Starting TAC Generation...")
        self.visit(node)
        print("⚙️ TAC Generation Finished.")
        return self.tac_code

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
        op_map = { '+': 'ADD', '-': 'SUB', '*': 'MUL', '/': 'DIV' }
        tac_op = op_map.get(node.get('op'))
        if not tac_op:

            print(f"⚠️ Warning: Unsupported binary operator '{node.get('op')}' encountered in TAC gen.")
            return self.new_temp() 

        left_result = self.visit(node.get('left'))
        right_result = self.visit(node.get('right'))


        if left_result is None or right_result is None:
             print(f"⚠️ Warning: Operands for '{tac_op}' were None.")
             return self.new_temp() 

        result_temp = self.new_temp()
        self.add_instruction(tac_op, left_result, right_result, result_temp)
        return result_temp

    def visit_Variable(self, node):
        return node.get('name')

    def visit_Number(self, node):
        return node.get('value')

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
             print("⚠️ Warning: Failed to evaluate condition in ForLoop.")
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
    print(f"📄 Reading file: {input_file}")
    try:
        with open(input_file, 'r') as f:
            source_code = f.read()
    except FileNotFoundError:
        print(f"❌ Error: Input file '{input_file}' not found.")
        sys.exit(1) 

    print("\n L E X I N G . . .")
    try:
        tokens = list(lex(source_code)) 
        print(f"✅ Lexing successful ({len(tokens)} tokens found).")
    except SyntaxError as e:
         print(f"\n❌ Syntax Error during lexical analysis: {e}")
         sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected Error during Lexical Analysis: {e}")
        sys.exit(1)

    print("\n P A R S I N G . . .")
    parser = SyntaxAnalyzer(tokens)
    try:
        ast = parser.parse()
        print("✅ Parsing successful.")
        try:
            with open(ast_file, "w") as f: json.dump(ast, f, indent=4)
        except IOError: pass 
    except SyntaxError as e:
        print(f"\n❌ Syntax Error during parsing: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected Error during Parsing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n S E M A N T I C   A N A L Y S I S . . .")
    semantic_analyzer = SemanticAnalyzer(ast)
    try:
        symbol_table, errors = semantic_analyzer.analyze()
        try:
            with open(sym_table_file, "w") as f: json.dump(symbol_table, f, indent=4)
        except IOError: pass

        if errors:
            print("\n❌ Semantic Errors Found:")
            for error in errors:
                print(f"  - {error}")
            print("Aborting before TAC generation due to semantic errors.")
            sys.exit(1) 
        else:
            print("\n✅ No Semantic Errors Found.")


    except Exception as e:
        print(f"\n❌ An unexpected error occurred during Semantic Analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n T A C   G E N E R A T I O N . . .")
    generator = TACGenerator()
    try:
        tac_instructions = generator.generate(ast)
        print("✅ TAC generation successful.")

        print("\n📝 Generated TAC Instructions:")
        output_lines = []
        for i, instruction in enumerate(tac_instructions):
            op = instruction['op']
            arg1 = instruction.get('arg1', '')
            arg2 = instruction.get('arg2', '')
            result = instruction.get('result', '')
            line = ""
            if op.startswith("IF_"):
                 line = f"{i:03d}:  if {arg1} {op.split('_')[1]} {arg2} goto {result}"
            elif op == "GOTO":
                line = f"{i:03d}:  goto {arg1}"
            elif op == "LABEL":
                line = f"{i:03d}: {arg1}:"
            elif op == "ASSIGN":
                line = f"{i:03d}:  {result} = {arg1}"
            elif op in ['ADD', 'SUB', 'MUL', 'DIV']:
                op_symbol = {'ADD':'+', 'SUB':'-', 'MUL':'*', 'DIV':'/'}.get(op, op)
                line = f"{i:03d}:  {result} = {arg1} {op_symbol} {arg2}"
            else:
                line = f"{i:03d}:  {op} {arg1} {arg2} {result}" 
            print(line)
            output_lines.append(line)

        try:
            with open(tac_output_file, 'w') as f:
                 f.write('\n'.join(output_lines))
            print(f"\n✅ TAC saved to {tac_output_file}")
        except IOError:
            print(f"❌ Error: Could not write TAC to {tac_output_file}")

    except Exception as e:
        print(f"\n❌ An unexpected error occurred during TAC Generation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n--- COMPILER PIPELINE FINISHED ---")


if __name__ == "__main__":
    main()