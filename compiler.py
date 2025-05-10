import json
from pprint import pprint
import sys
import os

from Lexical_Analyzer import lex
from Syntax_analyzer import SyntaxAnalyzer, pretty_print_ast, visualize_ast_with_anytree, ANYTREE_AVAILABLE
from Semantic_analyzer import SemanticAnalyzer 
from tac_generator import TACGenerator 
from tac_optimizer import TACOptimizer

def main():
    input_file = "input.txt"
    tokens_file = "tokens.txt"
    derivation_log_file = "derivation_log.txt"
    ast_file = "AST.json"
    symbol_table_file = "symbol_table.json"
    tac_file = "tac_optimized.txt"
    tac_original_file = "tac_original.txt"

    try:
        with open(input_file, 'r') as f:
            source_code = f.read()
    except FileNotFoundError:
        print(f"Error: file '{input_file}' not found.", file=sys.stderr)
        sys.exit(1)

    try:
        tokens = list(lex(source_code))
        with open(tokens_file, 'w') as f:
            for token in tokens:
                f.write(f"{token}\n")
    except Exception as e:
        print(f"Lexical error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        parser = SyntaxAnalyzer(tokens, log_derivation=True)
        ast = parser.parse()
        parser.print_derivation_log(filename=derivation_log_file)
        with open(ast_file, 'w') as f:
            json.dump(ast, f, indent=4)
    except Exception as e:
        print(f"Syntax error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        semantic_analyzer = SemanticAnalyzer(ast)
        symbol_table, semantic_errors = semantic_analyzer.analyze()
        with open(symbol_table_file, 'w') as f:
            json.dump(symbol_table, f, indent=4)
        if semantic_errors:
            for error in semantic_errors:
                print(f"- {error}\n")
            print("Semantic errors found.", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"Semantic analysis error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        tac_generator = TACGenerator()
        tac, _ = tac_generator.generate(ast)
        with open("tactable.json", 'w') as f:
            json.dump(tac, f)

        def format_line(i, instr):
            op, a1, a2, res = instr['op'], instr.get('arg1',''), instr.get('arg2',''), instr.get('result','')
            if op == "LABEL":
                return f"{i:03d}:  {res}:"
            elif op == "GOTO":
                return f"{i:03d}:  goto {res}"
            elif op == "ASSIGN":
                return f"{i:03d}:  {res} = {a1}"
            elif op == "UMINUS":
                return f"{i:03d}:  {res} = -{a1}"
            elif op in ["ADD", "SUB", "MUL", "DIV"]:
                sym_map = {"ADD": "+", "SUB": "-", "MUL": "*", "DIV": "/"}
                sym = sym_map.get(op, op)
                return f"{i:03d}:  {res} = {a1} {sym} {a2}"
            elif op == "CONCAT":
                return f"{i:03d}:  {res} = {a1} + {a2}"
            elif op in ["LT", "GT", "LE", "GE", "EQ", "NE"]:
                symbol = {"LT": "<", "GT": ">", "LE": "<=", "GE": ">=", "EQ": "==", "NE": "!="}.get(op, op)
                return f"{i:03d}:  {res} = {a1} {symbol} {a2}"
            elif op == "IF_FALSE":
                return f"{i:03d}:  IF {a1} false goto {res}"
            else:
                return f"{i:03d}:  {op} {a1}, {a2}, {res}"

        original_lines = []
        for i, instr in enumerate(tac):
            original_lines.append(format_line(i, instr))
        with open(tac_original_file, 'w') as f:
            f.write('\n'.join(original_lines))

        optimizer = TACOptimizer(tac)
        optimized = optimizer.optimize()

        final_lines = []
        for i, instr in enumerate(optimized):
            final_lines.append(format_line(i, instr))
        with open(tac_file, 'w') as f:
            f.write('\n'.join(final_lines))

    except Exception as e:
        print(f"3AC error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
