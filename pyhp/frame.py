from rpython.rlib import jit
from pyhp.reference import Reference


class BaseVarMap(object):
    _settled_ = True

    def get_reference(self, name):
        raise NotImplementedError

    def load(self, name):
        raise NotImplementedError

    def store(self, name, value):
        raise NotImplementedError


class VarMap(BaseVarMap):
    _immutable_fields_ = ['vars', 'parent', 'scope']

    def __init__(self, size, parent):
        self.vars = [None] * size
        self.parent = parent

    def store(self, name, value):
        index = self.scope.get_index(name)
        self.vars[index] = value

    def load(self, name):
        index = self.scope.get_index(name)
        return self.vars[index]

    def get_reference(self, name):
        if self.scope.has(name):
            return Reference(self, name)
        else:
            return self.parent.get_reference(name)


class GlobalVarMap(BaseVarMap):
    _immutable_fields_ = ['functions[*]']

    def __init__(self, functions):
        functions_ = {}
        for function in functions:
            functions_[function.name] = function
        self.functions = functions_

    @jit.elidable_promote("0")
    def has(self, name):
        return name in self.functions

    def get_reference(self, name):
        if self.has(name):
            return Reference(self, name)
        raise Exception("%s reference not found" % name)

    def load(self, name):
        return self.functions[name]


class Frame(object):
    _settled_ = True
    _immutable_fields_ = ['valuestack', 'refs', 'varmap', 'code',
                          'arguments[*]']
    _virtualizable_ = ['valuestack[*]', 'valuestack_pos', 'refs[*]']

    def __init__(self, code):
        self = jit.hint(self, access_directly=True, fresh_virtualizable=True)
        self.valuestack = [None] * 10  # safe estimate!
        self.valuestack_pos = 0

        self.code = code

        self.refs = [None] * code.env_size()

    @jit.unroll_safe
    def declare(self):
        code = jit.promote(self.code)

        self.varmap.scope = code.variables()

        if code.is_function_code() and self.arguments:
            # set call arguments as variable values
            param_index = 0
            for variable in code.params():
                self.varmap.store(variable, self.arguments[param_index])
                param_index += 1

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

    def get_reference(self, name, index=-1):
        if index < 0:
            return self.varmap.get_reference(name)

        ref = self._get_refs(index)

        if ref is None:
            ref = self.varmap.get_reference(name)
            self._set_refs(index, ref)

        return ref

    def _get_refs(self, index):
        assert index < len(self.refs)
        assert index >= 0
        return self.refs[index]

    def _set_refs(self, index, value):
        assert index < len(self.refs)
        assert index >= 0
        self.refs[index] = value

    def __repr__(self):
        return "Frame %s" % (self.varmap)


class GlobalFrame(Frame):
    def __init__(self, code, global_varmap):
        Frame.__init__(self, code)

        self.varmap = VarMap(code.env_size(), global_varmap)

        self.declare()


class FunctionFrame(Frame):
    def __init__(self, code, arguments=None, parent_varmap=None):
        Frame.__init__(self, code)

        self.varmap = VarMap(code.env_size(), parent_varmap)

        self.arguments = arguments

        self.declare()

    def argv(self):
        return self.arguments
