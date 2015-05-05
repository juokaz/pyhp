from rpython.rlib import jit
from pyhp.reference import Reference


class VarMap(object):
    _immutable_fields_ = ['vars', 'parent', 'scope']

    def __init__(self, size, scope):
        self.vars = [None] * size
        self.scope = scope

    def store(self, name, value):
        assert name is not None and isinstance(name, str)
        scope = self.scope
        index = scope.lookup(name)
        self.vars[index] = value

    def load(self, name):
        assert name is not None and isinstance(name, str)
        scope = self.scope
        index = scope.lookup(name)
        return self.vars[index]

    def get_reference(self, name):
        if self.scope.contains(name):
            return Reference(self, name)
        else:
            return None

    def __repr__(self):
        return 'VarMap(%s)' % (self.vars)


class Frame(object):
    _settled_ = True
    _immutable_fields_ = ['valuestack', 'refs', 'varmap', 'code', 'space',
                          'arguments[*]']
    _virtualizable_ = ['valuestack[*]', 'valuestack_pos', 'refs[*]']

    def __init__(self, space, code):
        self = jit.hint(self, access_directly=True, fresh_virtualizable=True)
        self.valuestack = [None] * 10  # safe estimate!
        self.valuestack_pos = 0

        self.code = code
        self.space = space

        self.refs = [None] * code.env_size()

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
            if self.varmap.scope.contains(name):
                index = self.varmap.scope.lookup(name)
            else:
                raise Exception('Frame has no variable %s' % name)

        ref = self._get_refs(index)

        if ref is None:
            ref = self.varmap.get_reference(name)
            self._set_refs(index, ref)

        return ref

    def set_reference(self, name, index, ref):
        if index < 0:
            if self.varmap.scope.contains(name):
                index = self.varmap.scope.lookup(name)
            else:
                raise Exception('Frame has no variable %s' % name)

        self._set_refs(index, ref)

    def _get_refs(self, index):
        assert index < len(self.refs)
        assert index >= 0
        return self.refs[index]

    def _set_refs(self, index, value):
        assert index < len(self.refs)
        assert index >= 0
        self.refs[index] = value

    def declare_function(self, name, func):
        self.space.declare_function(name, func)

    def get_function(self, name):
        return self.space.get_function(name)

    def declare_constant(self, name, value):
        self.space.declare_constant(name, value)

    def get_constant(self, name):
        return self.space.get_constant(name)

    def __repr__(self):
        return "Frame %s" % (self.code)


class GlobalFrame(Frame):
    def __init__(self, space, code):
        Frame.__init__(self, space, code)

        self.varmap = VarMap(code.env_size(), code.symbols())


class FunctionFrame(Frame):
    def __init__(self, space, parent_frame, code, arguments=None):
        Frame.__init__(self, space, code)
        assert isinstance(parent_frame, Frame)

        self.varmap = VarMap(code.env_size(), code.symbols())

        self.arguments = arguments

        self.declare(parent_frame)

    @jit.unroll_safe
    def declare(self, parent_frame):
        code = jit.promote(self.code)

        # set call arguments as variable values
        param_index = 0
        for param, by_value in code.params():
            argument = self.arguments[param_index]
            if by_value:
                # todo use copy.deepcopy for this
                argument = argument.__deepcopy__()
            self.varmap.store(param, argument)
            param_index += 1

        # every variable referenced in 'globals' needs to be initialized
        for name in code.globals():
            ref = parent_frame.get_reference(name)
            self.set_reference(name, -1, ref)

    def argv(self):
        return self.arguments
