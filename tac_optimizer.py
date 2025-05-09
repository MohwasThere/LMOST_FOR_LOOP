class TACOptimizer:
    def __init__(self, tac):
        self.original_tac = tac
        self.optimized_tac = []

    def optimize(self):
        tac = self.constant_folding(self.original_tac)
        tac = self.constant_propagation(tac)
        tac = self.common_subexpression_elimination(tac)
        tac = self.strength_reduction(tac)
        tac = self.dead_code_elimination(tac)
        self.optimized_tac = tac
        return tac

    def constant_folding(self, tac):
        new_tac = []
        for instr in tac:
            if instr['op'] in {'ADD', 'SUB', 'MUL', 'DIV'}:
                if isinstance(instr['arg1'], (int, float)) and isinstance(instr['arg2'], (int, float)):
                    result = eval(f"{instr['arg1']} {self.op_to_symbol(instr['op'])} {instr['arg2']}")
                    new_tac.append({'op': 'ASSIGN', 'arg1': result, 'arg2': None, 'result': instr['result']})
                    continue
            new_tac.append(instr)
        return new_tac

    def constant_propagation(self, tac):
        # First pass: collect all reassigned variables
        reassigned = set()
        assigned_once = {}

        for instr in tac:
            if instr['op'] == 'ASSIGN':
                var = instr.get('result')
                if var:
                    if var in assigned_once:
                        reassigned.add(var)
                    else:
                        assigned_once[var] = instr.get('arg1')

        # Second pass: propagate only safe constants
        const_vals = {var: val for var, val in assigned_once.items() if var not in reassigned}
        new_tac = []

        for instr in tac:
            instr = instr.copy()

            for key in ['arg1', 'arg2']:
                val = instr.get(key)
                if isinstance(val, str) and val in const_vals:
                    instr[key] = const_vals[val]

            new_tac.append(instr)

        return new_tac



    def common_subexpression_elimination(self, tac):
        expr_map = {}
        new_tac = []
        for instr in tac:
            if instr['op'] in {'ADD', 'SUB', 'MUL', 'DIV'}:
                key = (instr['op'], instr['arg1'], instr['arg2'])
                if key in expr_map:
                    new_tac.append({'op': 'ASSIGN', 'arg1': expr_map[key], 'arg2': None, 'result': instr['result']})
                else:
                    expr_map[key] = instr['result']
                    new_tac.append(instr)
            else:
                new_tac.append(instr)
        return new_tac

    def strength_reduction(self, tac):
        new_tac = []
        for instr in tac:
            if instr['op'] == 'MUL' and instr['arg2'] == 2:
                new_tac.append({'op': 'ADD', 'arg1': instr['arg1'], 'arg2': instr['arg1'], 'result': instr['result']})
                continue
            new_tac.append(instr)
        return new_tac

    def dead_code_elimination(self, tac):
        used = set()
        for instr in tac:
            if instr.get('arg1'):
                used.add(instr['arg1'])
            if instr.get('arg2'):
                used.add(instr['arg2'])
            if instr['op'] in ['IF_FALSE', 'GOTO']:
                if instr.get('result'):
                    used.add(instr['result'])

        new_tac = []
        for instr in reversed(tac):
            op = instr['op']
            result = instr.get('result')

            # Always keep control flow or label
            if op in ['LABEL', 'GOTO', 'IF_FALSE'] or (result and result in used):
                new_tac.insert(0, instr)
                if instr.get('arg1'):
                    used.add(instr['arg1'])
                if instr.get('arg2'):
                    used.add(instr['arg2'])
            elif op == 'ASSIGN' and result in used:
                new_tac.insert(0, instr)
                if instr.get('arg1'):
                    used.add(instr['arg1'])

        return new_tac


    def op_to_symbol(self, op):
        return {'ADD': '+', 'SUB': '-', 'MUL': '*', 'DIV': '/'}[op]
