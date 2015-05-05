from pyhp.datatypes import W_Root, W_CodeFunction

class ObjectSpace(object):
    def __init__(self, global_functions):
        self.functions = {}
        self.constants = {}

        self._declare_global_functions(global_functions)

    def _declare_global_functions(self, functions):
        for func in functions:
            self.declare_function(func.name, func)

    def declare_function(self, name, func):
        assert isinstance(name, str)
        assert isinstance(func, W_CodeFunction)
        self.functions[name] = func

    def get_function(self, name):
        assert isinstance(name, str)
        return self.functions.get(name, None)

    def declare_constant(self, name, value):
        assert isinstance(name, str)
        self.constants[name] = value

    def get_constant(self, name):
        assert isinstance(name, str)
        return self.constants.get(name, None)
