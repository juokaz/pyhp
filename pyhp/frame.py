from rpython.rlib import jit


class BaseVarMap(object):
    _settled_ = True

    def get(self, name):
        raise NotImplementedError

    def get_index(self, name):
        raise NotImplementedError

    def set(self, name, value):
        raise NotImplementedError


class VarMap(BaseVarMap):
    _immutable_fields_ = ['vars[*]', 'parent', 'scope']

    def __init__(self, size, parent):
        self.vars = [None] * size
        self.parent = parent

    def get_index(self, name):
        index = self.scope.get_index(name)
        return jit.promote(index)

    def get(self, name):
        assert isinstance(name, str)
        if self.get_scope().has_global(name):
            return self.parent.get(name)

        if self.get_scope().has_variable(name) \
                or self.get_scope().has_function(name):
            return self.load(name)

        return self.parent.get(name)

    def set(self, name, value):
        assert isinstance(name, str)
        if self.get_scope().has_global(name):
            return self.parent.set(name, value)

        if self.get_scope().has_variable(name) \
                or self.get_scope().has_function(name):
            return self.store(name, value)

        return self.parent.set(name, value)

    def store(self, name, value):
        index = self.get_index(name)
        self.vars[index] = value

    def load(self, name):
        index = self.get_index(name)
        return self.vars[index]

    def get_scope(self):
        return self.scope


class GlobalVarMap(BaseVarMap):
    _immutable_fields_ = ['functions[*]']

    def __init__(self, functions):
        functions_ = {}
        for function in functions:
            functions_[function.name] = function
        self.functions = functions_

    def get(self, name):
        return self.functions[name]

    def set(self, name, value):
        raise Exception("Global varmap cannot accept var sets")


class Frame(object):
    _settled_ = True
    _immutable_fields_ = ['valuestack', 'varmap', 'code', 'arguments[*]']
    _virtualizable_ = ['valuestack[*]', 'valuestack_pos']

    def __init__(self, code):
        self = jit.hint(self, access_directly=True, fresh_virtualizable=True)
        self.valuestack = [None] * 10  # safe estimate!
        self.valuestack_pos = 0

        self.code = code

    @jit.unroll_safe
    def declare(self):
        code = jit.promote(self.code)

        self.varmap.scope = code.get_scope()

        if code.is_function_code() and self.arguments:
            # set call arguments as variable values
            param_index = 0
            for variable in code.params():
                index = self.get_index(variable)
                self.set_var(index, variable, self.arguments[param_index])
                param_index += 1

    def get_var(self, name, index=-1):
        return self.varmap.get(name)

    def set_var(self, index, name, value):
        assert index >= 0

        self.varmap.set(name, value)

    def get_varmap(self):
        return self.varmap

    def get_index(self, name):
        return self.varmap.get_index(name)

    def push(self, v):
        pos = self.get_pos()
        len_stack = len(self.valuestack)

        # prevent stack overflow
        assert pos >= 0 and len_stack > pos

        self.valuestack[pos] = v
        self.valuestack_pos = pos + 1

    def pop(self):
        v = self.top()
        pos = self.get_pos() - 1
        assert pos >= 0
        self.valuestack[pos] = None
        self.valuestack_pos = pos
        return v

    @jit.unroll_safe
    def pop_n(self, n):
        if n < 1:
            return []

        r = []
        i = n
        while i > 0:
            i -= 1
            e = self.pop()
            r = [e] + r

        return r

    def top(self):
        pos = self.get_pos() - 1
        assert pos >= 0
        return self.valuestack[pos]

    def get_pos(self):
        return jit.promote(self.valuestack_pos)

    def __repr__(self):
        return "Frame %s" % (self.varmap)


class GlobalFrame(Frame):
    def __init__(self, code, global_varmap):
        Frame.__init__(self, code)

        self.varmap = VarMap(code.env_size(), global_varmap)

        self.declare()


class FunctionFrame(Frame):
    def __init__(self, code, arguments=None, parent_context=None):
        Frame.__init__(self, code)

        self.varmap = VarMap(code.env_size(), parent_context.get_varmap())

        self.arguments = arguments

        self.declare()

    def argv(self):
        return self.arguments
