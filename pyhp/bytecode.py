from pyhp.opcodes import opcodes, LABEL, BaseJump, DECLARE_FUNCTION
from rpython.rlib import jit


class ByteCode(object):
    _immutable_fields_ = ['compiled_opcodes[*]', '_symbols', '_variables[*]',
                          '_globals[*]', '_parameters[*]', '_superglobals[*]',
                          'name']

    def __init__(self, name, scope):
        self.name = name
        self.opcodes = []
        self._symbols = scope.symbols
        self._variables = scope.variables[:]
        self._globals = scope.globals[:]
        self._parameters = scope.parameters[:]
        self._superglobals = scope.superglobals[:]

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

    def symbols(self):
        return self._symbols

    def variables(self):
        return self._variables

    def superglobals(self):
        return self._superglobals

    def globals(self):
        return self._globals

    def params(self):
        return self._parameters

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

    def _functions(self):
        """Returns the bytecode of all functions defined"""
        functions = []
        for opcode in self.opcodes:
            if isinstance(opcode, DECLARE_FUNCTION):
                functions.append(opcode.bytecode)
        return functions

    def __str__(self):
        return self.str()

    def str(self):
        lines = []

        for function in self._functions():
            lines.append(u'Function ' + function.str())
            lines.append(u'')

        if self.name.find(".php") != -1:
            lines.append(self.name + u':')
        else:
            arguments = []
            for param, by_value in self.params():
                if by_value:
                    arguments.append(param)
                else:
                    arguments.append(u'&' + param)
            lines.append(self.name + u'(' + u", ".join(arguments) + u'):')
        for index, opcode in enumerate(self.opcodes):
            lines.append(u"%d: %s" % (index, opcode.str()))
        return u"\n".join(lines)


def compile_ast(ast, symbols, name):
    bc = ByteCode(name, symbols)
    if ast is not None:
        ast.compile(bc)
    bc.compile()
    return bc
