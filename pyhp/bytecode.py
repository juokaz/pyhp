from pyhp.opcodes import opcodes


class ByteCode(object):
    _immutable_fields_ = ['opcodes[*]', 'symbols', 'parameters[:]']

    def __init__(self, symbols):
        self.opcodes = []
        self.symbols = symbols
        self.parameters = symbols.parameters[:]

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
    # print 'Bytecode: '
    # print bc
    return bc
