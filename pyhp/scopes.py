from pyhp.symbols import new_map

SUPERGLOBALS = [u'$_GET', u'$_POST']
SUPERGLOBAL_LOOKUP = {}
for i, v in enumerate(SUPERGLOBALS):
    SUPERGLOBAL_LOOKUP[v] = i


class Scope(object):
    def __init__(self):
        self.symbols = new_map()
        self.variables = []
        self.globals = []
        self.parameters = []
        self.superglobals = [-1] * len(SUPERGLOBALS)

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

        # remember which index the superglobal variable is identified as
        if name in SUPERGLOBALS:
            self.superglobals[SUPERGLOBAL_LOOKUP[name]] = idx

        return idx

    def add_global(self, name):
        idx = self.add_symbol(name)

        if name not in self.globals:
            self.globals.append(name)

        return idx

    def add_parameter(self, name, by_value):
        idx = self.add_symbol(name)

        if (name, by_value) not in self.parameters:
            self.parameters.append((name, by_value))

        return idx

    def finalize(self):
        return FinalScope(self.symbols, self.variables[:], self.globals[:],
                          self.parameters[:], self.superglobals[:])


class FinalScope(object):
    _immutable_fields_ = ['symbols', 'variables[*]', 'globals[*]',
                          'parameters[*]', 'superglobals[*]']

    def __init__(self, symbols, variables, globals, parameters, superglobals):
        self.symbols = symbols
        self.variables = variables
        self.globals = globals
        self.parameters = parameters
        self.superglobals = superglobals
