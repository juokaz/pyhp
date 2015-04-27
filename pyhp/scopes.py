from rpython.rlib import jit


class SymbolsMap(object):
    def __init__(self):
        self.symbols = []
        self.symbols_id = {}

    def add(self, name):
        if name not in self.symbols_id:
            self.symbols_id[name] = len(self.symbols)
            self.symbols.append(name)
            idx = len(self.symbols) - 1
        else:
            idx = self.symbols_id[name]

        assert isinstance(idx, int)
        assert idx >= 0
        return idx

    def finalize(self):
        return StaticSymbolsMap(self.symbols[:], self.symbols_id)


class StaticSymbolsMap(object):
    _immutable_fields_ = ['symbols[*]', 'symbols_id[*]']

    def __init__(self, symbols, symbols_id):
        self.symbols = symbols
        self.symbols_id = symbols_id

    @jit.elidable_promote("0")
    def get_index(self, name):
        if name in self.symbols_id:
            return self.symbols_id[name]
        else:
            return -1

    @jit.elidable_promote("0")
    def has(self, name):
        return (self.get_index(name) == -1) is False

    def __len__(self):
        return len(self.symbols)


class Scope(object):
    def __init__(self):
        self.symbols = SymbolsMap()
        self.functions = []
        self.variables = []
        self.globals = []
        self.parameters = []

    def add_symbol(self, name):
        return self.symbols.add(name)

    def add_variable(self, name):
        idx = self.add_symbol(name)

        self.variables.append(name)
        return idx

    def add_global(self, name):
        idx = self.add_symbol(name)

        self.globals.append(name)
        return idx

    def add_parameter(self, name):
        idx = self.add_symbol(name)

        self.parameters.append(name)
        return idx

    def add_function(self, name):
        idx = self.add_symbol(name)

        self.functions.append(name)
        return idx

    def finalize(self):
        # these variables and those functions are the only identifiers
        # this scope defines, everything else comes from a parent
        variables = [v for v in self.variables[:] if v not in self.globals]
        functions = self.functions[:]
        symbols = SymbolsMap()
        for identifier in variables + functions:
            symbols.add(identifier)
        return FinalScope(len(self.symbols.finalize()), symbols.finalize(),
                          self.parameters[:])


class FinalScope(object):
    _immutable_fields_ = ['size', 'variables' 'parameters[*]']

    def __init__(self, size, variables, parameters):
        self.size = size
        self.variables = variables
        self.parameters = parameters
