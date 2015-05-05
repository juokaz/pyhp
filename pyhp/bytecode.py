"""This file contains both an interpreter and "hints" in the interpreter code
necessary to construct a Jit.

There are two required hints:
1. JitDriver.jit_merge_point() at the start of the opcode dispatch loop
2. JitDriver.can_enter_jit() at the end of loops (where they jump back)

These bounds and the "green" variables effectively mark loops and
allow the jit to decide if a loop is "hot" and in need of compiling.

Read http://doc.pypy.org/en/latest/jit/pyjitpl5.html for details.

"""

from pyhp.opcodes import opcodes, LABEL, BaseJump
from rpython.rlib import jit

from pyhp.datatypes import W_Null, W_Root


def printable_loc(pc, bc):
    bytecode = bc._get_opcode(pc)
    return str(pc) + ": " + str(bytecode)

driver = jit.JitDriver(greens=['pc', 'self'],
                       reds=['frame', 'result'],
                       virtualizables=['frame'],
                       get_printable_location=printable_loc)


class ByteCode(object):
    _immutable_fields_ = ['compiled_opcodes[*]', '_symbol_size', '_symbols',
                          'parameters[*]', '_globals[*]']

    def __init__(self, scope):
        self.opcodes = []
        self._symbol_size = scope.size
        self._symbols = scope.symbols
        self._globals = scope.globals[:]
        self.parameters = scope.parameters[:]

        self.label_count = 100000
        self.startlooplabel = []
        self.endlooplabel = []
        self.pop_after_break = []
        self.updatelooplabel = []

    def compile(self):
        self.unlabel()
        self.compiled_opcodes = [o for o in self.opcodes]

    def unlabel(self):
        labels = {}
        counter = 0
        for i in range(len(self.opcodes)):
            op = self.opcodes[i]
            if isinstance(op, LABEL):
                labels[op.num] = counter
            else:
                counter += 1

        self.opcodes = [o for o in self.opcodes if not isinstance(o, LABEL)]
        for op in self.opcodes:
            if isinstance(op, BaseJump):
                op.where = labels[op.where]

    def variables(self):
        return self._symbols

    def globals(self):
        return self._globals

    def params(self):
        return self.parameters

    def symbol_size(self):
        return self._symbol_size

    def emit_label(self, num=-1):
        if num == -1:
            num = self.prealocate_label()
        self.emit('LABEL', num)
        return num

    def emit_startloop_label(self):
        num = self.emit_label()
        self.startlooplabel.append(num)
        return num

    def prealocate_label(self):
        num = self.label_count
        self.label_count += 1
        return num

    def prealocate_endloop_label(self, pop_after_break=False):
        num = self.prealocate_label()
        self.endlooplabel.append(num)
        self.pop_after_break.append(pop_after_break)
        return num

    def prealocate_updateloop_label(self):
        num = self.prealocate_label()
        self.updatelooplabel.append(num)
        return num

    def emit_endloop_label(self, label):
        self.endlooplabel.pop()
        self.startlooplabel.pop()
        self.pop_after_break.pop()
        self.emit_label(label)

    def emit_updateloop_label(self, label):
        self.updatelooplabel.pop()
        self.emit_label(label)

    def emit_break(self):
        if not self.endlooplabel:
            raise Exception("Break outside loop")
        self.emit('JUMP', self.endlooplabel[-1])

    def emit_continue(self):
        if not self.startlooplabel:
            raise Exception("Continue outside loop")
        self.emit('JUMP', self.updatelooplabel[-1])

    def continue_at_label(self, label):
        self.updatelooplabel.append(label)

    def done_continue(self):
        self.updatelooplabel.pop()

    def emit(self, bc, *args):
        opcode = getattr(opcodes, bc)(*args)
        self.opcodes.append(opcode)
        return opcode
    emit._annspecialcase_ = 'specialize:arg(1)'

    @jit.elidable
    def _get_opcode(self, pc):
        assert pc >= 0
        return self.compiled_opcodes[pc]

    @jit.elidable
    def _opcode_count(self):
        return len(self.compiled_opcodes)

    def execute(self, frame):
        if self._opcode_count() == 0:
            return W_Null()

        pc = 0
        result = None
        while True:
            # required hint indicating this is the top of the opcode dispatch
            driver.jit_merge_point(pc=pc, self=self, frame=frame,
                                   result=result)

            if pc >= self._opcode_count():
                break

            opcode = self._get_opcode(pc)
            result = opcode.eval(frame)

            if isinstance(result, W_Root):
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

    def __repr__(self):
        lines = []
        for index, opcode in enumerate(self.opcodes):
            lines.append(str(index) + ": " + str(opcode))
        return "\n".join(lines)


def compile_ast(ast, symbols):
    bc = ByteCode(symbols)
    if ast is not None:
        ast.compile(bc)
    # print 'Bytecode: '
    # print bc
    return bc
