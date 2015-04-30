from pyhp.symbols import new_map


class Scope(object):
    def __init__(self):
        self.symbols = new_map()
        self.functions = []
        self.variables = []
        self.globals = []
        self.constants = []
        self.parameters = []

    def add_symbol(self, name):
        idx = self.symbols.lookup(name)

        if idx == self.symbols.NOT_FOUND:
            self.symbols = self.symbols.add(name)
            idx = self.symbols.lookup(name)

        assert isinstance(idx, int)
        return idx

    def add_variable(self, name):
        idx = self.add_symbol(name)

        if name not in self.variables:
            self.variables.append(name)

        return idx

    def add_global(self, name):
        idx = self.add_symbol(name)

        if name not in self.globals:
            self.globals.append(name)

        return idx

    def add_constant(self, name):
        idx = self.add_symbol(name)

        if name not in self.constants:
            self.constants.append(name)

        return idx

    def add_parameter(self, name, by_value):
        idx = self.add_symbol(name)

        if (name, by_value) not in self.parameters:
            self.parameters.append((name, by_value))

        return idx

    def add_function(self, name):
        idx = self.add_symbol(name)

        if name not in self.functions:
            self.functions.append(name)

        return idx

    def finalize(self, main=False):
        # these variables and those functions are the only identifiers
        # this scope defines, everything else comes from a parent
        variables = [v for v in self.variables[:] if v not in self.globals]
        functions = self.functions[:]
        variables = variables + functions
        if main:
            variables += self.constants[:]
        symbols = new_map()
        for identifier in variables:
            symbols = symbols.add(identifier)
        return FinalScope(self.symbols.len(), symbols,
                          self.parameters[:])


class FinalScope(object):
    _immutable_fields_ = ['size', 'variables' 'parameters[*]']

    def __init__(self, size, variables, parameters):
        self.size = size
        self.variables = variables
        self.parameters = parameters
