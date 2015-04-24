"""This file contains both an interpreter and "hints" in the interpreter code
necessary to construct a Jit.

There are two required hints:
1. JitDriver.jit_merge_point() at the start of the opcode dispatch loop
2. JitDriver.can_enter_jit() at the end of loops (where they jump back)

These bounds and the "green" variables effectively mark loops and
allow the jit to decide if a loop is "hot" and in need of compiling.

Read http://doc.pypy.org/en/latest/jit/pyjitpl5.html for details.

"""

from pyhp.opcodes import opcodes
from rpython.rlib import jit

from pyhp.datatypes import W_Null
from pyhp.opcodes import BaseJump


def printable_loc(pc, bc):
    bytecode = bc.get_opcode(pc)
    return str(pc) + " " + str(bytecode)

driver = jit.JitDriver(greens=['pc', 'self'],
                       reds=['frame', 'result'],
                       virtualizables=['frame'],
                       get_printable_location=printable_loc)


class ByteCode(object):
    _immutable_fields_ = ['compiled_opcodes[*]', 'symbols', 'parameters[*]']

    def __init__(self, symbols):
        self.opcodes = []
        self.symbols = symbols
        self.parameters = symbols.parameters[:]

    def compile(self):
        self.compiled_opcodes = [o for o in self.opcodes]

    def get_symbols(self):
        return self.symbols

    def get_opcode(self, pc):
        return self.compiled_opcodes[pc]

    def get_name(self, index):
        return self.symbols.get_name(index)

    def functions(self):
        return self.symbols.functions

    def params(self):
        return self.parameters

    def emit(self, bc, *args):
        opcode = getattr(opcodes, bc)(*args)
        self.opcodes.append(opcode)
        return opcode
    emit._annspecialcase_ = 'specialize:arg(1)'

    def execute(self, frame):
        pc = 0
        result = None
        while True:
            # required hint indicating this is the top of the opcode dispatch
            driver.jit_merge_point(pc=pc, self=self, frame=frame,
                                   result=result)

            if pc >= len(self.compiled_opcodes):
                break

            opcode = self.get_opcode(pc)
            result = opcode.eval(frame)

            if result is not None:
                break

            if isinstance(opcode, BaseJump):
                new_pc = opcode.do_jump(frame, pc)
                if new_pc < pc:
                    driver.can_enter_jit(pc=new_pc, self=self,
                                         frame=frame, result=result)
                pc = new_pc
                continue
            else:
                pc += 1

        if result is None:
            result = W_Null()

        return result

    def __len__(self):
        return len(self.opcodes)

    def __repr__(self):
        lines = []
        index = 0
        for opcode in self.opcodes:
            lines.append("%s: %s" % (index, opcode))
            index += 1
        return "\n".join(lines)


def compile_ast(ast, symbols):
    bc = ByteCode(symbols)
    if ast is not None:
        ast.compile(bc)
    bc.compile()
    # print 'Bytecode: '
    # print bc
    return bc
