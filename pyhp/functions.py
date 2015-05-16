class BaseFunction(object):
    _settled_ = True

    def run(self, interpreter, frame):
        raise NotImplementedError

    def symbols(self):
        return None

    def globals(self):
        return []

    def params(self):
        return []

    def name(self):
        return '_unnamed_'

    def is_function_code(self):
        return False

    def env_size(self):
        return 0


class NativeFunction(BaseFunction):
    _immutable_fields_ = ['_name', 'function']

    def __init__(self, name, function):
        assert isinstance(name, unicode)
        self._name = name
        self.function = function

    def name(self):
        return self._name

    def run(self, interpreter, frame):
        return self.function(interpreter, frame.argv())


class ExecutableCode(BaseFunction):
    _immutable_fields_ = ['bytecode']

    def __init__(self, bytecode):
        from pyhp.bytecode import ByteCode
        assert isinstance(bytecode, ByteCode)
        self.bytecode = bytecode
        self.bytecode.compile()

    def get_bytecode(self):
        return self.bytecode

    def run(self, interpreter, frame):
        code = self.get_bytecode()
        result = interpreter.execute(code, frame)
        return result

    def symbols(self):
        code = self.get_bytecode()
        return code.symbols()

    def globals(self):
        code = self.get_bytecode()
        return code.globals()

    def params(self):
        code = self.get_bytecode()
        return code.params()

    def env_size(self):
        code = self.get_bytecode()
        return code.symbols().len()

    def __repr__(self):
        return "ExecutableCode %s" % (self.bytecode)


class GlobalCode(ExecutableCode):
    pass


class CodeFunction(ExecutableCode):
    _immutable_fields_ = ['bytecode', '_name']

    def __init__(self, name, bytecode):
        assert isinstance(name, unicode)
        ExecutableCode.__init__(self, bytecode)
        self._name = name

    def name(self):
        return self._name

    def is_function_code(self):
        return True
