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

    def get_index(self, name):
        return self.symbols_id[name]

    def get_name(self, index):
        return self.symbols[index]

    def __len__(self):
        return len(self.symbols)


class Scope(object):
    def __init__(self, symbols_map):
        self.symbols = symbols_map
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
        return FinalScope(self.symbols.finalize(), self.functions[:],
                          self.variables[:], self.globals[:],
                          self.parameters[:])


class FinalScope(object):
    _immutable_fields_ = ['symbols', 'functions[*]', 'variables[*]',
                          'globals[*]', 'parameters[*]']

    def __init__(self, symbols, functions, variables, globals, parameters):
        self.symbols = symbols
        self.functions = functions
        self.variables = variables
        self.globals = globals
        self.parameters = parameters

    @jit.elidable_promote("0")
    def get_index(self, name):
        assert isinstance(name, str)
        return self.symbols.get_index(name)

    @jit.elidable_promote("0")
    def get_name(self, name):
        assert isinstance(name, str)
        return self.symbols.get_name(name)

    @jit.elidable_promote("0")
    def has_variable(self, name):
        assert isinstance(name, str)
        return name in self.variables

    @jit.elidable_promote("0")
    def has_global(self, name):
        assert isinstance(name, str)
        return name in self.globals

    @jit.elidable_promote("0")
    def has_function(self, name):
        assert isinstance(name, str)
        return name in self.functions

    def get_symbols(self):
        return self.symbols

    def __len__(self):
        return len(self.symbols)
