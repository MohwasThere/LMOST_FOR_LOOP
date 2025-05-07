class TACOptimizer:
    def __init__(self, tac):
        self.original_tac = tac
        self.optimized_tac = []
        self.constants = {}
        self.expr_map = {}

    def optimize(self):
        tac = self.constant_folding(self.original_tac)
        tac = self.constant_propagation(tac)
        tac = self.common_subexpression_elimination(tac)
        tac = self.strength_reduction(tac)
        tac = self.dead_code_elimination(tac)
        # More passes can be added here
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
        const_vals = {}
        new_tac = []
        for instr in tac:
            if instr['op'] == 'ASSIGN' and isinstance(instr['arg1'], (int, float)):
                const_vals[instr['result']] = instr['arg1']
            for key in ['arg1', 'arg2']:
                if instr.get(key) in const_vals:
                    instr[key] = const_vals[instr[key]]
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
            if instr['op'] == 'MUL':
                if instr['arg2'] == 2:
                    new_tac.append({'op': 'ADD', 'arg1': instr['arg1'], 'arg2': instr['arg1'], 'result': instr['result']})
                    continue
            new_tac.append(instr)
        return new_tac

    def dead_code_elimination(self, tac):
        used = set()
        for instr in tac:
            if instr['arg1']: used.add(instr['arg1'])
            if instr['arg2']: used.add(instr['arg2'])

        new_tac = []
        for instr in reversed(tac):
            if instr['result'] in used or instr['op'] == 'LABEL':
                new_tac.insert(0, instr)
        return new_tac

    def op_to_symbol(self, op):
        return {'ADD': '+', 'SUB': '-', 'MUL': '*', 'DIV': '/'}[op]
