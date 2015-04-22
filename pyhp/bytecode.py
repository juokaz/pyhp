
bytecodes = ['LOAD_CONSTANT', 'LOAD_VAR', 'LOAD_FUNCTION',
             'LOAD_NULL', 'LOAD_BOOLEAN', 'LOAD_INTVAL', 'LOAD_FLOATVAL',
             'LOAD_STRINGVAL',
             'LOAD_ARRAY', 'LOAD_MEMBER', 'STORE_MEMBER',
             'ASSIGN', 'DISCARD_TOP',
             'JUMP_IF_FALSE', 'JUMP_BACKWARD', 'BINARY_ADD', 'BINARY_SUB',
             'BINARY_EQ', 'BINARY_GE', 'BINARY_LT', 'RETURN', 'PRINT',
             'BINARY_STRINGJOIN',
             'LOAD_PARAM', 'CALL',

             'ADD', 'SUB', 'MUL', 'DIV', 'INCR', 'DECR', 'MOD',
             ]

BytecodesMap = {}

for i, bytecode in enumerate(bytecodes):
    globals()[bytecode] = i
    BytecodesMap[bytecode] = i


class Opcode(object):
    def __init__(self, bytecode, *args):
        self.bytecode = bytecode
        self.args = args

    def __repr__(self):
        bc = bytecodes[self.bytecode]

        if self.args:
            args = ""
            for arg in self.args:
                args += str(arg) + ", "
            args = args.strip(", ")
            return "%s %s" % (bc, args)
        else:
            return bc

class CompilerContext(object):
    def __init__(self):
        self.data = []

    def emit(self, bc, *args):
        opcode = Opcode(bc, *args)
        self.data.append(opcode)
        return opcode

    def create_bytecode(self, symbols):
        return ByteCode(self.data, symbols)


class ByteCode(object):
    _immutable_fields_ = ['opcodes[*]', 'symbols']

    def __init__(self, opcodes, symbols):
        self.opcodes = opcodes
        self.symbols = symbols

        #print 'Bytecode: '
        #print self

    def index_for_symbol(self, symbol):
        return self.symbols.get_index(symbol)

    def get_name(self, index):
        return self.symbols.get_name(index)

    def __repr__(self):
        lines = []
        index = 0
        for opcode in self.opcodes:
            lines.append("%s: %s" % (index, opcode))
            index += 1
        return '\n'.join(lines)


def compile_ast(astnode, symbols):
    c = CompilerContext()
    astnode.compile(c)
    c.emit(BytecodesMap['RETURN'])
    return c.create_bytecode(symbols)
