from pyhp.datatypes import NativeFunction


def strlen(string):
    return string.len()

functions = [
    NativeFunction('strlen', strlen)
]


class Scope(object):
    def __init__(self, functions):
        self.functions = functions

    def has_function(self, name):
        for function in self.functions:
            if function.name == name:
                return True
        return False

    def get_function(self, name):
        for function in self.functions:
            if function.name == name:
                return function
        raise Exception("Function %s not found" % name)


class StdLib(object):
    def __init__(self, functions):
        self.scope = Scope(functions)

    def get_var(self, index, name):
        return self.scope.get_function(name)

    def is_visible(self, name):
        # a global variable
        if self.scope.has_function(name):
            return True

        return False

stdlib = StdLib(functions)
