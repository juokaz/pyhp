
bytecodes = ['LOAD_CONSTANT', 'LOAD_VAR', 'LOAD_NULL', 'LOAD_BOOLEAN',
             'ASSIGN', 'DISCARD_TOP',
             'JUMP_IF_FALSE', 'JUMP_BACKWARD', 'BINARY_ADD', 'BINARY_SUB',
             'BINARY_EQ', 'BINARY_GE', 'BINARY_LT', 'RETURN', 'PRINT',
             'BINARY_STRINGJOIN',
             'LOAD_PARAM', 'CALL']

BytecodesMap = {}

for i, bytecode in enumerate(bytecodes):
    globals()[bytecode] = i
    BytecodesMap[bytecode] = i


class CompilerContext(object):
    def __init__(self):
        self.data = []
        self.constants = []
        self.names = []
        self.names_id = {}

        self.functions = []
        self.function_id = {}

    def register_constant(self, v):
        self.constants.append(v)
        return len(self.constants) - 1

    def register_var(self, name):
        try:
            return self.names_id[name]
        except KeyError:
            self.names_id[name] = len(self.names)
            self.names.append(name)
            return len(self.names) - 1

    def get_var(self, name):
        if name in self.names_id:
            return self.names_id[name]
        else:
            raise NameError('Variable `'+name+'` is not defined')

    def register_function(self, func):
        name = func.name.lower()
        if name in self.function_id:
            raise NameError('Function `%s` is already defined' % name)
        else:
            self.function_id[name] = [len(self.functions)]
            self.functions.append(func)
            return len(self.functions) - 1

    def resolve_function(self, name):
        name = name.lower()
        try:
            ids = self.function_id[name]
            return (ids[0], self.functions[ids[0]])
        except KeyError:
            raise NameError('Function `'+name+'` is not defined')

    def emit(self, bc, arg=0):
        self.data.append(chr(bc))
        self.data.append(chr(arg))

    def create_bytecode(self):
        return ByteCode("".join(self.data), self.constants[:],
                        self.functions[:], len(self.names))


class ByteCode(object):
    _immutable_fields_ = ['code', 'constants[*]', 'functions[*]', 'numvars']

    def __init__(self, code, constants, functions, numvars):
        self.code = code
        self.constants = constants
        self.functions = functions
        self.numvars = numvars

        # print 'Bytecode: '
        # print self.dump()

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
    c.emit(BytecodesMap['RETURN'])
    return c.create_bytecode()
