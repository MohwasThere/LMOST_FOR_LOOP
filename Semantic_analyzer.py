import json

class SemanticAnalyzer:
    def __init__(self, ast):
        self.ast = ast
        self.symbol_table = {}
        self.errors = []
        self.declared_vars = set() 
        self.current_scope_level = 0 

    def analyze(self):
        """
        Analyzes the provided AST, populates the symbol table, and collects errors.
        Returns:
            tuple: (symbol_table, errors_list)
        """
        self.visit(self.ast)
        return self.symbol_table, self.errors

    def visit(self, node):
        """Recursively visits nodes in the AST."""
        if isinstance(node, list):
            for item in node:
                self.visit(item)
        elif isinstance(node, dict) and 'type' in node:
            method_name = f'visit_{node["type"]}'
            visitor = getattr(self, method_name, self.generic_visit)
            visitor(node)
        elif isinstance(node, (str, int, float, bool)): 
            pass 
        elif node is None:
            pass
        else:
            print(f"Warning (Semantic Analyzer): Skipping unknown node structure: {type(node)} {str(node)[:100]}")

    def generic_visit(self, node):
        """Generic visitor for dictionary nodes not handled by specific visitors."""
        if isinstance(node, dict):
            for key, value in node.items():
                if isinstance(value, (dict, list)):
                    self.visit(value)

    def visit_Program(self, node):
        """Visits the Program node."""
        self.visit(node.get('body', []))

    def visit_Declaration(self, node):
        """Visits a Declaration node, adding variables to the symbol table."""
        var_name = node.get("var_name")
        var_type = node.get("var_type")

        supported_types = ['int', 'float', 'string', 'double', 'char', 'bool']

        if not var_name or not var_type:
            self.errors.append(f"Semantic Error: Invalid declaration node structure: {node}")
            return

        if var_name in self.declared_vars: 
            self.errors.append(f"Semantic Error: Variable '{var_name}' is already declared.")
        else:
            if var_type not in supported_types: 
                self.errors.append(f"Semantic Error: Unsupported declaration type '{var_type}' for '{var_name}'. Supported types are: {supported_types}")
                return
            self.declared_vars.add(var_name)
            self.symbol_table[var_name] = {"type": var_type, "initialized": False, "value": None, "scope": self.current_scope_level} 

    def visit_Assignment(self, node):
        """Visits an Assignment node, checking types and variable declaration.
           Updates variable's value in symbol table if assigned a literal."""
        var_name = node.get("var")
        expression_node = node.get("expr")

        if not var_name or expression_node is None:
            self.errors.append(f"Semantic Error: Invalid assignment node structure: {node}")
            return

        if var_name not in self.symbol_table:
            self.errors.append(f"Semantic Error: Variable '{var_name}' was not declared before assignment.")
            self.visit(expression_node) 
            return

        self.visit(expression_node) 
        expr_type = self.get_expression_type(expression_node)
        
        assigned_value = None 

        if isinstance(expression_node, dict) and 'type' in expression_node:
            expr_node_type = expression_node['type']
            if expr_node_type == 'Number': 
                try:
                    val_str = str(expression_node.get('value'))
                    if '.' in val_str or 'e' in val_str.lower(): 
                        assigned_value = float(val_str)
                    else:
                        assigned_value = int(val_str)
                except (ValueError, TypeError):
                    assigned_value = None 
            elif expr_node_type == 'StringLiteral':
                assigned_value = str(expression_node.get('value', ''))[1:-1]
            elif expr_node_type == 'CharLiteral': 
                char_val_str = str(expression_node.get('value', "''"))
                if len(char_val_str) == 3 and char_val_str.startswith("'") and char_val_str.endswith("'"):
                    if char_val_str[1] == '\\' and len(char_val_str) > 2: 
                        esc_map = {'n': '\n', 't': '\t', "'": "'", '"': '"', '\\': '\\'}
                        assigned_value = esc_map.get(char_val_str[2], char_val_str[2]) 
                    else:
                        assigned_value = char_val_str[1]
                else: 
                    self.errors.append(f"Semantic Error: Invalid char literal format for '{char_val_str}' in assignment to '{var_name}'.")
                    assigned_value = None 
            elif expr_node_type == 'BooleanLiteral':
                assigned_value = bool(expression_node.get('value', False)) 

        if expr_type != "Unknown": 
            declared_type = self.symbol_table[var_name]["type"]
            is_compatible = False

            if declared_type == expr_type:
                is_compatible = True
            elif declared_type == 'float':
                if expr_type in ['int', 'float', 'double']: is_compatible = True
            elif declared_type == 'double': 
                if expr_type in ['int', 'float', 'double']: is_compatible = True
            elif declared_type == 'bool': 
                if expr_type == 'bool': is_compatible = True
            elif declared_type == 'char': 
                if expr_type == 'char': is_compatible = True
            
            if not is_compatible:
                self.errors.append(f"Semantic Error: Type mismatch in assignment to '{var_name}'. Cannot assign '{expr_type}' to '{declared_type}'.")
            
            self.symbol_table[var_name]["initialized"] = True
            if assigned_value is not None:
                py_type_ok = False
                if declared_type == 'int' and isinstance(assigned_value, int): py_type_ok = True
                elif declared_type == 'float' and isinstance(assigned_value, (int, float)): py_type_ok = True 
                elif declared_type == 'double' and isinstance(assigned_value, (int, float)): py_type_ok = True
                elif declared_type == 'string' and isinstance(assigned_value, str): py_type_ok = True
                elif declared_type == 'char' and isinstance(assigned_value, str) and len(assigned_value) == 1: py_type_ok = True
                elif declared_type == 'bool' and isinstance(assigned_value, bool): py_type_ok = True
                
                if py_type_ok:
                    self.symbol_table[var_name]["value"] = assigned_value
                else:
                    self.errors.append(f"Semantic Error: Literal value '{assigned_value}' (Python type: {type(assigned_value).__name__}) is not directly storable as declared type '{declared_type}' for variable '{var_name}'.")
                    self.symbol_table[var_name]["value"] = None 
            else: 
                 self.symbol_table[var_name]["value"] = None
        else: 
            self.symbol_table[var_name]["initialized"] = True
            self.symbol_table[var_name]["value"] = None

    def visit_ForLoop(self, node):
        self.current_scope_level += 1
        if "init" in node: self.visit(node["init"])
        if "condition" in node: self.visit(node["condition"])
        if "update" in node: self.visit(node["update"])
        if "body" in node: self.visit(node["body"])
        self.current_scope_level -= 1

    def visit_Condition(self, node):
        left_node = node.get("left")
        right_node = node.get("right") 
        op = node.get("op") 

        if left_node is None or right_node is None or op is None:
            self.errors.append(f"Semantic Error: Invalid condition node structure for binary comparison: {node}")
            return

        self.visit(left_node)
        self.visit(right_node)

        left_type = self.get_expression_type(left_node)
        right_type = self.get_expression_type(right_node)

        if left_type != "Unknown" and right_type != "Unknown":
             numeric_types = {'int', 'float', 'double'}
             can_compare = False
             if left_type in numeric_types and right_type in numeric_types:
                 can_compare = True
             elif left_type == 'char' and right_type == 'char':
                 can_compare = True
             elif left_type == 'string' and right_type == 'string' and op in ['==', '!=']: 
                 can_compare = True
             elif left_type == 'bool' and right_type == 'bool' and op in ['==', '!=']: 
                 can_compare = True
            
             if not can_compare:
                 self.errors.append(f"Semantic Error: Incompatible types in condition ({op}). Cannot compare '{left_type}' and '{right_type}' with this operator.")

    def visit_BinaryExpr(self, node):
        left_node = node.get("left")
        right_node = node.get("right")
        op = node.get("op") 

        if left_node is None or right_node is None or op is None:
            self.errors.append(f"Semantic Error: Invalid binary expression structure: {node}")
            return
        
        self.visit(left_node)
        self.visit(right_node)
        
        left_type = self.get_expression_type(left_node)
        right_type = self.get_expression_type(right_node)

        if left_type != "Unknown" and right_type != "Unknown":
            numeric_types = {'int', 'float', 'double'}

            if op == '+':
                if left_type == "string" and right_type == "string": pass 
                elif left_type in numeric_types and right_type in numeric_types: pass 
                else:
                    self.errors.append(f"Semantic Error: Operator '+' cannot be used between '{left_type}' and '{right_type}'.")
            elif op in ['-', '*', '/']: 
                if not (left_type in numeric_types and right_type in numeric_types):
                    self.errors.append(f"Semantic Error: Operator '{op}' requires numeric types, but got '{left_type}' and '{right_type}'.")
                if op == '/' and isinstance(right_node, dict) and right_node.get("type") == "Number":
                    try:
                        val_str = str(right_node.get("value", "1")) 
                        if float(val_str) == 0:
                            self.errors.append(f"Semantic Error: Division by zero.")
                    except ValueError: pass 
            else: 
                 self.errors.append(f"Semantic Error: Unknown or unsupported binary operator '{op}' for types '{left_type}' and '{right_type}'.")

    def visit_UnaryExpr(self, node):
        op = node.get("op")
        operand_node = node.get("operand")

        if operand_node is None or op is None:
            self.errors.append(f"Semantic Error: Invalid unary expression structure: {node}")
            return
        
        self.visit(operand_node) 
        operand_type = self.get_expression_type(operand_node)

        if op == '-': 
            if operand_type not in ['int', 'float', 'double']:
                self.errors.append(f"Semantic Error: Unary operator '-' cannot be applied to type '{operand_type}'.")
        else: 
             self.errors.append(f"Semantic Error: Unsupported unary operator '{op}'.")

    def visit_Variable(self, node):
        var_name = node.get("name")
        if var_name not in self.symbol_table:
            self.errors.append(f"Semantic Error: Variable '{var_name}' used before declaration.")
        elif not self.symbol_table[var_name].get("initialized", False) :
            pass 

    def visit_Number(self, node):
        pass 
    def visit_StringLiteral(self, node):
        pass
    def visit_CharLiteral(self, node):
        value = node.get('value', '')
        if not (len(value) >= 2 and value.startswith("'") and value.endswith("'")): 
            self.errors.append(f"Semantic Error: Invalid char literal format: {value}. Expected format like 'x'.")
        elif len(value) == 3 and value[1] == '\\' and value[2] not in ['n', 't', "'", '"', '\\']: 
             self.errors.append(f"Semantic Error: Unknown escape sequence '\\{value[2]}' in char literal: {value}.")
        elif len(value) > 3 and not (value[1] == '\\' and len(value) == 4) : 
             if not (value[1] == '\\' and value[2] in ['n', 't', "'", '"', '\\'] and len(value) == 4 and value[3] == "'"): 
                 self.errors.append(f"Semantic Error: Char literal too long: {value}. Expected single character or valid escape sequence.")
        pass
    def visit_BooleanLiteral(self, node):
        if not isinstance(node.get('value'), bool):
             self.errors.append(f"Semantic Error: Invalid boolean literal value: {node.get('value')}. Expected true or false.")
        pass

    def get_expression_type(self, expr_node):
        node_type_attr = None
        if isinstance(expr_node, dict) and 'type' in expr_node:
             node_type_attr = expr_node["type"]
        elif isinstance(expr_node, int): return "int" 
        elif isinstance(expr_node, float): return "double" 

        if node_type_attr == "Number":
            value_str = str(expr_node.get('value', '')) 
            try:
                if '.' in value_str or 'e' in value_str.lower(): 
                    float(value_str) 
                    return "double" 
                else:
                    int(value_str) 
                    return "int"
            except ValueError:
                self.errors.append(f"Semantic Error: Invalid number format '{value_str}'.")
                return "Unknown"
        elif node_type_attr == "Variable":
            var_name = expr_node.get("name")
            return self.get_variable_type(var_name)
        elif node_type_attr == "BinaryExpr":
            left_type = self.get_expression_type(expr_node.get("left"))
            right_type = self.get_expression_type(expr_node.get("right"))
            op = expr_node.get("op")

            if left_type == "Unknown" or right_type == "Unknown": return "Unknown" 
            
            numeric_types = {'int', 'float', 'double'}
            if op == '+':
                if left_type == "string" and right_type == "string": return "string"
                if left_type in numeric_types and right_type in numeric_types:
                    if 'double' in (left_type, right_type): return "double"
                    if 'float' in (left_type, right_type): return "float"
                    return "int"
            elif op in ['-', '*', '/']:
                if left_type in numeric_types and right_type in numeric_types:
                    if op == '/' : 
                         return "double" if 'double' in (left_type, right_type) or 'float' in (left_type, right_type) else "float" 
                    if 'double' in (left_type, right_type): return "double"
                    if 'float' in (left_type, right_type): return "float"
                    return "int"
            return "Unknown" 
        elif node_type_attr == "StringLiteral":
            return "string"
        elif node_type_attr == "CharLiteral":
            val_str = expr_node.get('value', '')
            if not (isinstance(val_str, str) and len(val_str) >= 2 and val_str.startswith("'") and val_str.endswith("'")):
                self.errors.append(f"Semantic Error: Malformed CharLiteral node value: {val_str}")
                return "Unknown"
            inner_content = val_str[1:-1]
            if len(inner_content) == 1: 
                return "char"
            elif len(inner_content) == 2 and inner_content.startswith('\\'): 
                if inner_content[1] in ['n', 't', "'", '"', '\\']: 
                    return "char"
                else:
                    self.errors.append(f"Semantic Error: Unknown escape sequence in char literal '{val_str}'.")
                    return "Unknown"
            else: 
                self.errors.append(f"Semantic Error: Char literal '{val_str}' must be a single character or a valid escape sequence.")
                return "Unknown"

        elif node_type_attr == "BooleanLiteral":
            if isinstance(expr_node.get('value'), bool):
                return "bool"
            else: 
                self.errors.append(f"Semantic Error: BooleanLiteral node has non-boolean value: {expr_node.get('value')}")
                return "Unknown"
        elif node_type_attr == "UnaryExpr":
            operand_type = self.get_expression_type(expr_node.get("operand"))
            op = expr_node.get("op")
            if op == '-' and operand_type in ['int', 'float', 'double']:
                return operand_type 
            return "Unknown"
        else:
            return "Unknown"

    def get_variable_type(self, var_name):
        if var_name in self.symbol_table:
            return self.symbol_table[var_name]["type"]
        else:
            return "Unknown"
