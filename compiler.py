import json
from pprint import pprint
import sys
import os

from Lexical_Analyzer import lex
from Syntax_analyzer import SyntaxAnalyzer, pretty_print_ast, visualize_ast_with_anytree, ANYTREE_AVAILABLE
from Semantic_analyzer import SemanticAnalyzer 
from TAC_Generator import TACGenerator 

def main():
    """
    Main function to run the compiler pipeline.
    Outputs only error messages to the terminal.
    """
    input_file = "input.txt"
    tokens_file = "tokens.txt"
    derivation_log_file = "derivation_log.txt"
    ast_file = "AST.json"
    symbol_table_file = "symbol_table.json"
    semantic_errors_file = "semantic_errors.txt"
    tac_file = "tac_code.txt"

    try:
        with open(input_file, 'r') as f:
            source_code = f.read()
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found. Please create it and add your source code.", file=sys.stderr)
        sys.exit(1)
    except IOError as e:
        print(f"Error reading input file '{input_file}': {e}", file=sys.stderr)
        sys.exit(1)

    token_list = []
    try:
        tokens_generator = lex(source_code)
        token_list = list(tokens_generator)
        with open(tokens_file, 'w') as f:
            for token in token_list:
                f.write(f"{token}\n")
    except SyntaxError as e:
         print(f"Lexical Error: {e}", file=sys.stderr)
         sys.exit(1)
    except ImportError:
        print("Error: Could not import 'lex' from Lexical_Analyzer.py. Ensure the file exists and is in the correct path.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during Lexical Analysis: {e}", file=sys.stderr)
        sys.exit(1)
    
    if not token_list:
        print("No tokens generated. Aborting.", file=sys.stderr)
        sys.exit(1)

    ast = None
    try:
        parser = SyntaxAnalyzer(token_list, log_derivation=True) 
        ast = parser.parse()
        parser.print_derivation_log(filename=derivation_log_file) 
        with open(ast_file, "w") as f:
            json.dump(ast, f, indent=4)
    except SyntaxError as e:
        print(f"Syntax Error: {e}", file=sys.stderr)
        if 'parser' in locals(): 
            parser.print_derivation_log(filename=derivation_log_file) 
        sys.exit(1)
    except ImportError:
        print("Error: Could not import from Syntax_analyzer.py. Ensure the file exists and is in the correct path.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during Syntax Analysis: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr) 
        if 'parser' in locals():
            parser.print_derivation_log(filename=derivation_log_file)
        sys.exit(1)

    if ast is None:
        print("AST not generated due to parsing errors. Skipping Semantic Analysis.", file=sys.stderr)
        sys.exit(1)
        
    symbol_table, semantic_errors = None, []
    try:
        semantic_analyzer = SemanticAnalyzer(ast) 
        symbol_table, semantic_errors = semantic_analyzer.analyze()
        with open(symbol_table_file, "w") as f:
            json.dump(symbol_table, f, indent=4)
        if semantic_errors:
            print("\nSemantic Errors Found:", file=sys.stderr)
            with open(semantic_errors_file, "w") as f:
                for error in semantic_errors:
                    print(f"  - {error}", file=sys.stderr) 
                    f.write(f"- {error}\n")
            print("Compilation aborted due to semantic errors.", file=sys.stderr)
            sys.exit(1) 
    except ImportError:
        print("Error: Could not import from Semantic_analyzer.py. Ensure the file exists and is in the correct path.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during Semantic Analysis: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

    if not ast or semantic_errors: 
        sys.exit(1) 

    tac_instructions, string_data_map = [], {} 
    try:
        tac_generator = TACGenerator()
        tac_instructions, string_data_map = tac_generator.generate(ast) 
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
            
            line_num_str = f"{i:03d}:  " 

            line = ""
            if op.startswith("IF_"): 
                 if op == "IF_FALSE": 
                     line = f"{line_num_str}if_false {arg1_str} goto {result_str}"
                 else: 
                     op_suffix = op.split('_', 1)[1] 
                     line = f"{line_num_str}if {arg1_str} {op_suffix} {arg2_str} goto {result_str}"
            elif op in ['LT', 'GT', 'LE', 'GE', 'EQ', 'NE']: 
                op_symbol_map = {'LT':'<', 'GT':'>', 'LE':'<=', 'GE':'>=', 'EQ':'==', 'NE':'!='}
                line = f"{line_num_str}{result_str} = {arg1_str} {op_symbol_map.get(op, op)} {arg2_str}"
            elif op == "GOTO":
                line = f"{line_num_str}goto {result_str}" 
            elif op == "LABEL":
                line = f"{line_num_str}{result_str}:" 
            elif op == "ASSIGN":
                line = f"{line_num_str}{result_str} = {arg1_str}"
            elif op == "UMINUS":
                 line = f"{line_num_str}{result_str} = - {arg1_str}"
            elif op in ['ADD', 'SUB', 'MUL', 'DIV', 'CONCAT']: 
                op_symbol_map = {'ADD':'+', 'SUB':'-', 'MUL':'*', 'DIV':'/', 'CONCAT': '+'} 
                op_sym = op_symbol_map.get(op, op) 
                line = f"{line_num_str}{result_str} = {arg1_str} {op_sym} {arg2_str}"
            else: 
                line = f"{line_num_str}{op} {arg1_str}, {arg2_str}, {result_str}" 
            output_lines.append(line.strip())
        
        with open(tac_file, 'w') as f:
            f.write('\n'.join(output_lines))

    except ImportError:
        print(f"Error: Could not import from TAC_Generator.py (or your TAC module filename). Ensure the file exists and is in the correct path.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during TAC Generation: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
