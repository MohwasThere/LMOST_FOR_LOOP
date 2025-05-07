import json
import sys 

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

    def new_string_label(self, string_value_with_quotes):
        actual_string = string_value_with_quotes[1:-1] 
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
        self.visit(node)
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
        elif isinstance(node, (str, int, float, bool)): 
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
        expr_result_var = self.visit(node.get('expr')) 

        if expr_result_var is not None: 
            self.add_instruction('ASSIGN', expr_result_var, None, var_name)
        else:
            print(f"Warning (TAC): Expression for assignment to '{var_name}' did not yield a result.", file=sys.stderr)
        return None 

    def visit_BinaryExpr(self, node):
        op = node.get('op')
        left_result_var = self.visit(node.get('left'))
        right_result_var = self.visit(node.get('right'))

        if left_result_var is None or right_result_var is None:
             return self.new_temp() 

        result_temp = self.new_temp()
        tac_op_map = {'+': 'ADD', '-': 'SUB', '*': 'MUL', '/': 'DIV'} 

        if op in tac_op_map:
            is_left_str = isinstance(left_result_var, str) and left_result_var.startswith('_str')
            is_right_str = isinstance(right_result_var, str) and right_result_var.startswith('_str')

            if op == '+' and (is_left_str or is_right_str):
                self.add_instruction('CONCAT', left_result_var, right_result_var, result_temp)
            else: 
                 self.add_instruction(tac_op_map[op], left_result_var, right_result_var, result_temp)
        else:
            print(f"Warning (TAC): Unsupported binary operator '{op}' skipped in TAC generation.", file=sys.stderr)
            return result_temp 
        return result_temp 

    def visit_UnaryExpr(self, node):
        op = node.get("op")
        operand_result_var = self.visit(node.get("operand"))

        if operand_result_var is None:
            return self.new_temp() 

        if op == '-': 
            result_temp = self.new_temp()
            self.add_instruction('UMINUS', operand_result_var, None, result_temp)
            return result_temp
        else:
            print(f"Warning (TAC): Unsupported unary operator '{op}' skipped.", file=sys.stderr)
            return operand_result_var 
        return operand_result_var 

    def visit_Variable(self, node):
        return node.get('name')

    def visit_Number(self, node):
        value = node.get('value')
        try: 
            if isinstance(value, str): 
                if '.' in value or 'e' in value.lower():
                    return float(value)
                return int(value)
            return value 
        except ValueError:
            print(f"Warning (TAC): Invalid number value '{value}' encountered for TAC.", file=sys.stderr)
            return 0 

    def visit_StringLiteral(self, node):
        string_value_with_quotes = node.get('value')
        string_label = self.new_string_label(string_value_with_quotes)
        return string_label 

    def visit_CharLiteral(self, node):
        char_literal_with_quotes = node.get('value') 
        if len(char_literal_with_quotes) >= 2 and char_literal_with_quotes.startswith("'") and char_literal_with_quotes.endswith("'"):
            inner_char = char_literal_with_quotes[1:-1]
            if len(inner_char) == 2 and inner_char.startswith('\\'): # Escape sequence
                esc_map = {'n': '\n', 't': '\t', "'": "'", '"': '"', '\\': '\\'}
                actual_char = esc_map.get(inner_char[1], inner_char[1])
                return ord(actual_char)
            elif len(inner_char) == 1: # Single character
                return ord(inner_char)
        print(f"Warning (TAC): Malformed char literal '{char_literal_with_quotes}' encountered.", file=sys.stderr)
        return 0 

    def visit_BooleanLiteral(self, node):
        bool_value = node.get('value') 
        return 1 if bool_value else 0

    def visit_Condition(self, node):
        left_result_var = self.visit(node.get('left'))
        right_result_var = self.visit(node.get('right'))
        return (left_result_var, node.get('op'), right_result_var)

    def visit_ForLoop(self, node):
        if node.get('init'):
            self.visit(node.get('init')) 
        start_loop_label = self.new_label() 
        body_label = self.new_label()       
        after_loop_label = self.new_label() 
        self.add_instruction('LABEL', None, None, start_loop_label)
        condition_parts = self.visit(node.get('condition'))
        if condition_parts:
            cond_left, cond_op, cond_right = condition_parts
            cond_temp = self.new_temp()
            rel_op_to_tac = {
                '<': 'LT', '>': 'GT', '<=': 'LE', '>=': 'GE', '==': 'EQ', '!=': 'NE'
            }
            if cond_op in rel_op_to_tac:
                self.add_instruction(rel_op_to_tac[cond_op], cond_left, cond_right, cond_temp)
            else: 
                print(f"Warning (TAC): Unknown relational operator '{cond_op}' in ForLoop condition.", file=sys.stderr)
                self.add_instruction('ASSIGN', 0, None, cond_temp) 
            self.add_instruction('IF_FALSE', cond_temp, None, after_loop_label)
        else:
             print("Warning (TAC): ForLoop condition is missing or invalid. Generating unconditional jump past loop.", file=sys.stderr)
             self.add_instruction('GOTO', None, None, after_loop_label)

        self.add_instruction('LABEL', None, None, body_label)
        if node.get('body'):
            self.visit(node.get('body'))
        if node.get('update'):
            self.visit(node.get('update'))
        self.add_instruction('GOTO', None, None, start_loop_label)
        self.add_instruction('LABEL', None, None, after_loop_label)
        return None
