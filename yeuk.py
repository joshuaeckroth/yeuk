import readline
from lark import Lark, Transformer, v_args

grammar = """
    ?start: statement*

    ?statement: conditional
              | assignment

    ?conditional: "if(" boolexpr ")" "{" statement* "}" -> conditional_if
                | "if(" boolexpr ")" "{" statement* "}" "else" "{" statement* "}" -> conditional_if_else

    ?boolexpr: expr "<" expr -> boolexpr_lt
             | expr ">" expr -> boolexpr_gt
             | expr "<=" expr -> boolexpr_le
             | expr ">=" expr -> boolexpr_ge

    ?assignment: NAME "=" expr ";" -> assign_var

    ?expr: subexpr
         | subexpr "+" expr -> add
         | subexpr "-" expr -> sub

    ?subexpr: NUMBER -> number
            | NAME -> lookup_var
            | "-" subexpr -> neg
            | "(" expr ")"

    NAME: /[a-z]/

    %import common.NUMBER
    %import common.WS
    %ignore WS
"""

@v_args(inline=True)
class ParseTree(Transformer):

    def __init__(self):
        self.freeregs = set(["x"+str(i) for i in range(1, 32)])
        self.vars = {}
        self.sp = 0
        self.last_label = 0

    def print(self, instructions):
        for v, loc in self.vars.items():
            print(f"# x == {loc}(sp)")
        print()
        print(f"addi sp, sp, -{self.sp}")
        for ins in instructions:
            print(ins[1])
        print(f"addi sp, sp, {self.sp}")

    def choose_reg(self):
        if len(self.freeregs) == 0:
            raise Exception("Out of registers!")
        else:
            reg = self.freeregs.pop()
            return reg

    def free_reg(self, reg):
        self.freeregs.add(reg)

    def lookup_var_loc(self, varname):
        if varname in self.vars:
            return self.vars[varname]
        else:
            self.vars[varname] = self.sp
            self.sp += 4
            return self.vars[varname]

    def make_label(self):
        self.last_label += 1
        return f"L{self.last_label}"

    def assign_var(self, varname, ins):
        var_loc = self.lookup_var_loc(varname)
        reg = ins[-1][0]
        self.free_reg(reg)
        return ins + [(None, f"sw {reg}, {var_loc}(sp)")]

    def lookup_var(self, varname):
        reg = self.choose_reg()
        var_loc = self.lookup_var_loc(varname)
        return [(reg, f"lw {reg}, {var_loc}(sp)")]

    def boolexpr_lt(self, left_ins, right_ins):
        left_reg = left_ins[-1][0]
        right_reg = right_ins[-1][0]
        return left_ins + right_ins + [(None, f"bge {left_reg}, {right_reg}")]

    def boolexpr_gt(self, left_ins, right_ins):
        left_reg = left_ins[-1][0]
        right_reg = right_ins[-1][0]
        return left_ins + right_ins + [(None, f"ble {left_reg}, {right_reg}")]
        return f"ble {left_reg}, {right_reg}"

    def boolexpr_le(self, left_ins, right_ins):
        left_reg = left_ins[-1][0]
        right_reg = right_ins[-1][0]
        return left_ins + right_ins + [(None, f"blt {right_reg}, {left_reg}")]

    def boolexpr_ge(self, left_ins, right_ins):
        left_reg = left_ins[-1][0]
        right_reg = right_ins[-1][0]
        return left_ins + right_ins + [(None, f"blt {left_reg}, {right_reg}")]

    def conditional_if(self, branchins, ins):
        skip_label = self.make_label()
        branchpart = branchins[-1][1]
        branchins = branchins[:-1]
        return branchins + [(None, f"{branchpart}, {skip_label}")] + ins + [(None, f"{skip_label}:")]

    def conditional_if_else(self, branchins, ins_if, ins_else):
        skip_label1 = self.make_label()
        skip_label2 = self.make_label()
        branchpart = branchins[-1][1]
        branchins = branchins[:-1]
        return branchins + [(None, f"{branchpart}, {skip_label1}")] + ins_if + \
                [(None, f"jal ra, {skip_label2}")] + [(None, f"{skip_label1}:")] + ins_else + [(None, f"{skip_label2}:")]

    def number(self, n):
        reg = self.choose_reg()
        return [(reg, f"addi {reg}, zero, {n}")]

    def neg(self, right_ins):
        reg = self.choose_reg()
        right_reg = right_ins[-1][0]
        self.free_reg(right_reg)
        return right_ins + [(reg, f"sub {reg}, zero, {right_reg}")]

    def add(self, left_ins, right_ins):
        reg_result = self.choose_reg()
        left_reg = left_ins[-1][0]
        right_reg = right_ins[-1][0]
        self.free_reg(left_reg)
        self.free_reg(right_reg)
        return left_ins + right_ins + [(reg_result, f"add {reg_result}, {left_reg}, {right_reg}")]

    def sub(self, left_ins, right_ins):
        reg_result = self.choose_reg()
        left_reg = left_ins[-1][0]
        right_reg = right_ins[-1][0]
        self.free_reg(left_reg)
        self.free_reg(right_reg)
        return left_ins + right_ins + [(reg_result, f"sub {reg_result}, {left_reg}, {right_reg}")]

pt = ParseTree()
parser = Lark(grammar, parser='lalr', transformer=pt)

while True:
    s = input("> ").strip()
    if len(s) == 0:
        break
    try:
        instructions = parser.parse(s)
        pt.print(instructions)
    except Exception as e:
        print(e)


