
bytecodes = ['LOAD_CONSTANT', 'LOAD_VAR', 'ASSIGN', 'DISCARD_TOP',
             'JUMP_IF_FALSE', 'JUMP_BACKWARD', 'BINARY_ADD', 'BINARY_SUB',
             'BINARY_EQ', 'RETURN', 'PRINT', 'BINARY_LT']
for i, bytecode in enumerate(bytecodes):
    globals()[bytecode] = i

BINOP = {'+': BINARY_ADD, '-': BINARY_SUB, '==': BINARY_EQ, '<': BINARY_LT}

class CompilerContext(object):
    def __init__(self):
        self.data = []
        self.constants = []
        self.names = []
        self.names_to_numbers = {}

    def register_constant(self, v):
        self.constants.append(v)
        return len(self.constants) - 1

    def register_var(self, name):
        try:
            return self.names_to_numbers[name]
        except KeyError:
            self.names_to_numbers[name] = len(self.names)
            self.names.append(name)
            return len(self.names) - 1

    def emit(self, bc, arg=0):
        self.data.append(chr(bc))
        self.data.append(chr(arg))

    def create_bytecode(self):
        return ByteCode("".join(self.data), self.constants[:], len(self.names))

class ByteCode(object):
    _immutable_fields_ = ['code', 'constants[*]', 'numvars']

    def __init__(self, code, constants, numvars):
        self.code = code
        self.constants = constants
        self.numvars = numvars

    def dump(self):
        lines = []
        i = 0
        for i in range(0, len(self.code), 2):
            c = self.code[i]
            c2 = self.code[i + 1]
            lines.append(bytecodes[ord(c)] + " " + str(ord(c2)))
        return '\n'.join(lines)

def compile_ast(astnode):
    c = CompilerContext()
    astnode.compile(c)
    c.emit(RETURN, 0)
    return c.create_bytecode()
