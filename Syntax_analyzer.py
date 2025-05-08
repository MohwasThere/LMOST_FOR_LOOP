import json

try:
    from anytree import Node, RenderTree
    ANYTREE_AVAILABLE = True
except ImportError:
    ANYTREE_AVAILABLE = False

class SyntaxAnalyzer:
    def __init__(self, tokens, log_derivation=False):
        self.tokens = list(tokens)
        self.pos = 0
        self.log_derivation_enabled = log_derivation
        self.derivation_steps = []
        self.indent_level = 0

    def _log(self, message):
        if self.log_derivation_enabled:
            self.derivation_steps.append("  " * self.indent_level + message)

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
                if self.log_derivation_enabled:
                     self.derivation_steps.append("  " * self.indent_level + f"Match terminal: '{token_value}' (Type: {token_type})")
                self.pos += 1
                return token_value
        return None

    def expect(self, expected_type=None, expected_value=None):
        expected_desc = f"'{expected_value}' ({expected_type})" if expected_value else f"type '{expected_type}'"
        token_value = self.match(expected_type, expected_value)

        if token_value is None:
            current_type, current_tok_val = self.current_token_info()
            found_desc = f"'{current_tok_val}' ({current_type})" if current_tok_val else "end of input"
            err_msg = f"Expected {expected_desc} but found {found_desc} at position {self.pos}"
            if self.log_derivation_enabled:
                self.derivation_steps.append("  " * self.indent_level + f"ERROR: {err_msg}")
            raise SyntaxError(err_msg)
        return token_value

    def parse(self):
        self._log("Start Symbol: <Program>")
        self.indent_level += 1
        self._log("Applying rule: Program -> StmtList")
        
        program_body = self.parse_stmt_list()
        
        if self.pos < len(self.tokens):
             if self.log_derivation_enabled:
                self.derivation_steps.append("  " * self.indent_level + f"Warning: Parsing finished but tokens remain at pos {self.pos}: {self.tokens[self.pos:]}")
        self.indent_level -= 1
        return {"type": "Program", "body": program_body}

    def parse_stmt_list(self):
        self.indent_level += 1
        stmts = []
        parsed_at_least_one_stmt = False
        declaration_keywords = ['int', 'float', 'string', 'double', 'char', 'bool']

        while True:
            if self.pos >= len(self.tokens):
                log_msg = "StmtList_Tail -> ε (end of input)" if parsed_at_least_one_stmt else "StmtList -> ε (end of input)"
                self._log(log_msg)
                break
            current_type, current_token = self.current_token_info()
            if current_token == '}':
                log_msg = "StmtList_Tail -> ε (found '}')" if parsed_at_least_one_stmt else "StmtList -> ε (found '}')"
                self._log(log_msg)
                break
            
            can_start_stmt = (current_token == 'for' and current_type == 'KEYWORD') or \
                             (current_token in declaration_keywords and current_type == 'KEYWORD') or \
                             (current_type == 'ID')

            if not can_start_stmt:
                log_msg = f"StmtList_Tail -> ε (token '{current_token}' cannot start Stmt)" if parsed_at_least_one_stmt else f"StmtList -> ε (token '{current_token}' cannot start Stmt)"
                self._log(log_msg)
                break
            log_msg_rule = "StmtList_Tail -> Stmt StmtList_Tail" if parsed_at_least_one_stmt else "StmtList -> Stmt StmtList_Tail"
            self._log(log_msg_rule)
            stmts.append(self.parse_stmt())
            parsed_at_least_one_stmt = True
        self.indent_level -= 1
        return stmts

    def parse_stmt(self):
        self.indent_level += 1
        stmt_node = None
        current_type, current_token = self.current_token_info()
        declaration_keywords = ['int', 'float', 'string', 'double', 'char', 'bool']

        if current_token == 'for' and current_type == 'KEYWORD':
            self._log("Applying rule: Stmt -> ForLoop")
            stmt_node = self.parse_for_loop()
        elif current_token in declaration_keywords and current_type == 'KEYWORD':
            self._log("Applying rule: Stmt -> Declaration")
            stmt_node = self.parse_declaration()
        elif current_type == 'ID':
            self._log("Applying rule: Stmt -> Assignment ;")
            stmt_node = self.parse_assignment()
            self.expect('SYMBOL', ';')
        else:
            err_msg = f"Unexpected token '{current_token}' ({current_type}) at position {self.pos}. Expected start of a statement (for, type, or ID)."
            if self.log_derivation_enabled:
                self.derivation_steps.append("  " * self.indent_level + f"ERROR: {err_msg}")
            raise SyntaxError(err_msg)
        self.indent_level -= 1
        return stmt_node

    def parse_declaration(self):
        self.indent_level += 1
        self._log("Applying rule: Declaration -> Type ID [= Expression] ;")

        var_type_token = self.expect('KEYWORD') 
        supported_types = ['int', 'float', 'string', 'double', 'char', 'bool']
        if var_type_token not in supported_types:
            raise SyntaxError(f"Expected type but found '{var_type_token}'")

        var_name = self.expect('ID')

        initializer = None
        if self.match('ASSIGN', '='):
            self._log("Detected initializer in declaration.")
            initializer = self.parse_expression()

        self.expect('SYMBOL', ';')
        self.indent_level -= 1

        if initializer:
            return {
                "type": "Declaration",
                "var_type": var_type_token,
                "var_name": var_name,
                "initializer": initializer
            }
        else:
            return {
                "type": "Declaration",
                "var_type": var_type_token,
                "var_name": var_name
            }


    def parse_for_loop(self):
        self.indent_level += 1
        self._log("Applying rule: ForLoop -> 'for' '(' Assignment ';' Condition ';' Assignment ')' '{' StmtList '}'")
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
        self.indent_level -= 1
        return {"type": "ForLoop", "init": init, "condition": cond, "update": update, "body": body}

    def parse_assignment(self):
        self.indent_level += 1
        self._log("Applying rule: Assignment -> ID = Expression")
        var_name = self.expect('ID')
        self.expect('ASSIGN', '=')
        expr = self.parse_expression()
        self.indent_level -= 1
        return {"type": "Assignment", "var": var_name, "expr": expr}

    def parse_condition(self):
        self.indent_level += 1
        
        left_expr = self.parse_expression()
        
        current_type, current_token_val = self.current_token_info()
        if current_type == 'REL_OP':
            self._log("Applying rule: Condition -> Expression RelOp Expression")
            op = self.expect('REL_OP')
            right_expr = self.parse_expression()
            self.indent_level -= 1
            return {"type": "Condition", "left": left_expr, "op": op, "right": right_expr}
        else:
            op = self.expect('REL_OP') 
            right_expr = self.parse_expression()
            self._log("Applying rule: Condition -> Expression RelOp Expression") 
            self.indent_level -= 1
            return {"type": "Condition", "left": left_expr, "op": op, "right": right_expr}

    def parse_factor(self):
        self.indent_level += 1
        node = None
        token_type, token_value = self.current_token_info()

        if self.match('OP', '-'):
            self._log("Applying rule: Factor -> - Factor")
            operand = self.parse_factor()
            node = {"type": "UnaryExpr", "op": "-", "operand": operand}
        elif self.match('SYMBOL', '('):
            self._log("Applying rule: Factor -> ( Expression )")
            node = self.parse_expression()
            self.expect('SYMBOL', ')')
        elif token_type == 'ID':
            self._log("Applying rule: Factor -> ID")
            id_name = self.expect('ID')
            node = {"type": "Variable", "name": id_name}
        elif token_type == 'NUMBER':
            self._log("Applying rule: Factor -> NUMBER")
            num_val = self.expect('NUMBER')
            node = {"type": "Number", "value": num_val}
        elif token_type == 'STRING_LITERAL':
            self._log("Applying rule: Factor -> STRING_LITERAL")
            str_val = self.expect('STRING_LITERAL')
            node = {"type": "StringLiteral", "value": str_val}
        elif token_type == 'CHAR_LITERAL': 
            self._log("Applying rule: Factor -> CHAR_LITERAL")
            char_val = self.expect('CHAR_LITERAL')
            node = {"type": "CharLiteral", "value": char_val} 
        elif token_type == 'KEYWORD' and token_value == 'true': 
            self._log("Applying rule: Factor -> true")
            self.expect('KEYWORD', 'true')
            node = {"type": "BooleanLiteral", "value": True}
        elif token_type == 'KEYWORD' and token_value == 'false': 
            self._log("Applying rule: Factor -> false")
            self.expect('KEYWORD', 'false')
            node = {"type": "BooleanLiteral", "value": False}
        else:
            err_msg = f"Unexpected token '{token_value}' ({token_type}) at position {self.pos}. Expected a valid factor (ID, Number, Literal, '(', or unary op)."
            if self.log_derivation_enabled:
                 self.derivation_steps.append("  " * self.indent_level + f"ERROR: {err_msg}")
            raise SyntaxError(err_msg)
        self.indent_level -= 1
        return node

    def parse_term(self):
        self.indent_level += 1
        self._log("Applying rule: Term -> Factor Term'")
        node = self.parse_factor()
        temp_indent = self.indent_level 
        self.indent_level +=1 
        while True:
            current_type, token_value = self.current_token_info()
            if current_type == 'OP' and token_value in ['*', '/']: 
                self._log(f"Applying rule: Term' -> {token_value} Factor Term'")
                op = self.expect('OP', token_value)
                right = self.parse_factor()
                node = {"type": "BinaryExpr", "op": op, "left": node, "right": right}
            else:
                self._log("Applying rule: Term' -> ε")
                break
        self.indent_level = temp_indent
        self.indent_level -= 1
        return node

    def parse_expression(self):
        self.indent_level += 1
        self._log("Applying rule: Expression -> Term Expression'") 
        
        node = self.parse_term() 

        temp_indent = self.indent_level 
        self.indent_level +=1 
        while True:
            current_type, token_value = self.current_token_info()
            if current_type == 'OP' and token_value in ['+', '-']:
                self._log(f"Applying rule: Expression' -> {token_value} Term Expression'")
                op = self.expect('OP', token_value)
                right = self.parse_term() 
                node = {"type": "BinaryExpr", "op": op, "left": node, "right": right}
            else:
                self._log("Applying rule: Expression' -> ε")
                break
        self.indent_level = temp_indent

        self.indent_level -= 1
        return node

    def print_derivation_log(self, filename=None):
        if not self.log_derivation_enabled:
            msg = "\nDerivation logging was not enabled."
            if filename:
                try:
                    with open(filename, 'w') as f: f.write(msg + "\n")
                except IOError as e: print(f"Error writing derivation log status to {filename}: {e}")
            else: print(msg)
            return

        log_header = "--- Leftmost Derivation Log ---"
        log_footer = "------------------------------"
        log_content = self.derivation_steps if self.derivation_steps else ["No derivation steps were recorded."]

        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(log_header + "\n")
                    for step in log_content: f.write(step + "\n")
                    f.write(log_footer + "\n")
            except IOError as e:
                print(f"\nError saving derivation log to {filename}: {e}. Printing to console instead.")
                print("\n" + log_header)
                for step in log_content: print(step)
                print(log_footer)
        else:
            print("\n" + log_header)
            for step in log_content: print(step)
            print(log_footer)

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

def visualize_ast_with_anytree(ast_dict, label="AST"):
    if not ANYTREE_AVAILABLE:
        print("\nNote: 'anytree' library not found. Skipping tree visualization.")
        return
    def build_anytree_nodes(node_data, parent=None, name_hint="item"):
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
                    build_anytree_nodes(value, parent=current_node, name_hint=key)
        elif isinstance(node_data, list):
            list_node_label = f"{name_hint} (List[{len(node_data)}])"
            list_node = Node(list_node_label, parent=parent)
            for i, item in enumerate(node_data):
                build_anytree_nodes(item, parent=list_node, name_hint=f"item_{i}")
        else:
            Node(repr(node_data), parent=parent)
    root_node = Node(label)
    build_anytree_nodes(ast_dict, parent=root_node, name_hint=ast_dict.get('type', 'Program'))
    print("\nAbstract Syntax Tree (Visualization - requires 'anytree'):")
    for pre, _, node in RenderTree(root_node):
        print(f"{pre}{node.name}")
