from pyhp.bytecode import ByteCode


class BaseFunction(object):
    _settled_ = True

    def run(self, ctx):
        raise NotImplementedError

    def variables(self):
        return None

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
        assert isinstance(name, str)
        self._name = name
        self.function = function

    def name(self):
        return self._name

    def run(self, frame):
        return self.function(frame.argv())


class ExecutableCode(BaseFunction):
    _immutable_fields_ = ['bytecode', 'symbol_size']

    def __init__(self, bytecode):
        assert isinstance(bytecode, ByteCode)
        self.bytecode = bytecode
        self.bytecode.compile()
        self.symbol_size = bytecode.symbol_size()

    def get_bytecode(self):
        return self.bytecode

    def run(self, frame):
        code = self.get_bytecode()
        result = code.execute(frame)
        return result

    def variables(self):
        code = self.get_bytecode()
        return code.variables()

    def params(self):
        code = self.get_bytecode()
        return code.params()

    def env_size(self):
        return self.symbol_size


class GlobalCode(ExecutableCode):
    pass


class CodeFunction(ExecutableCode):
    _immutable_fields_ = ['bytecode', '_name']

    def __init__(self, name, bytecode):
        assert isinstance(name, str)
        ExecutableCode.__init__(self, bytecode)
        self._name = name

    def name(self):
        return self._name

    def is_function_code(self):
        return True
