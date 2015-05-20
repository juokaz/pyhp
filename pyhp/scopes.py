from pyhp.symbols import new_map
from pyhp.datatypes import W_IntObject, W_FloatObject, W_StringSubstitution, \
    W_StringObject

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
        self.constants = []
        self.constants_ints = {}
        self.constants_floats = {}
        self.constants_strings = {}

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

        if (name, idx) not in self.globals:
            self.globals.append((name, idx))

        return idx

    def add_parameter(self, name, by_value):
        idx = self.add_symbol(name)

        if (name, by_value) not in self.parameters:
            self.parameters.append((name, by_value))

        return idx

    def add_int_constant(self, value):
        try:
            return self.constants_ints[value]
        except KeyError:
            a = len(self.constants)
            self.constants.append(W_IntObject(value))
            self.constants_ints[value] = a
            return a

    def add_float_constant(self, value):
        try:
            return self.constants_floats[value]
        except KeyError:
            a = len(self.constants)
            self.constants.append(W_FloatObject(value))
            self.constants_floats[value] = a
            return a

    def add_string_constant(self, value):
        try:
            return self.constants_strings[value]
        except KeyError:
            a = len(self.constants)
            self.constants.append(W_StringObject(value))
            self.constants_strings[value] = a
            return a

    def add_string_substitution(self, value):
        a = len(self.constants)
        self.constants.append(W_StringSubstitution(value))
        return a
