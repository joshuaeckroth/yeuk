
from lark import Lark, Transformer, v_args

grammar = """
    ?start: expr

    ?expr: subexpr
         | subexpr "+" expr -> add
         | subexpr "-" expr -> sub

    ?subexpr: NUMBER -> number
            | "-" subexpr -> neg
            | "(" expr ")"

    %import common.NUMBER
    %import common.WS
    %ignore WS
"""

@v_args(inline=True)
class ParseTree(Transformer):

    def __init__(self):
        self.freeregs = set(["x"+str(i) for i in range(1, 32)])

    def choose_reg(self):
        if len(self.freeregs) == 0:
            raise Exception("Out of registers!")
        else:
            reg = self.freeregs.pop()
            return reg

    def free_reg(self, reg):
        self.freeregs.add(reg)

    def number(self, n):
        reg = self.choose_reg()
        print(f"addi {reg}, zero, {n}")
        return reg

    def neg(self, right_reg):
        reg = self.choose_reg()
        print(f"sub {reg}, zero, {right_reg}")
        self.free_reg(right_reg)
        return reg

    def add(self, left_reg, right_reg):
        reg_result = self.choose_reg()
        print(f"add {reg_result}, {left_reg}, {right_reg}")
        self.free_reg(left_reg)
        self.free_reg(right_reg)
        return reg_result

    def sub(self, left_reg, right_reg):
        reg_result = self.choose_reg()
        print(f"sub {reg_result}, {left_reg}, {right_reg}")
        self.free_reg(left_reg)
        self.free_reg(right_reg)
        return reg_result

parser = Lark(grammar, parser='lalr', transformer=ParseTree())

while True:
    s = input("> ").strip()
    if len(s) == 0:
        break
    parser.parse(s)


