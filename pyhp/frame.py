from rpython.rlib import jit
from pyhp.datatypes import W_Reference


class Frame(object):
    _settled_ = True
    _immutable_fields_ = ['code', 'space', 'symbols',
                          'arguments[*]']
    _virtualizable_ = ['valuestack[*]', 'valuestack_pos', 'vars[*]']

    def __init__(self, space, code):
        self = jit.hint(self, access_directly=True, fresh_virtualizable=True)
        self.valuestack = [None] * 10  # safe estimate!
        self.valuestack_pos = 0

        self.vars = [None] * code.env_size()

        self.code = code
        self.space = space
        self.symbols = code.symbols()

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

    def _store(self, index, value):
        assert isinstance(index, int)
        assert index >= 0
        self.vars[index] = value

    def _load(self, index):
        assert isinstance(index, int)
        assert index >= 0
        return self.vars[index]

    def set_reference(self, name, index, value):
        if index < 0:
            if self.symbols.contains(name):
                index = self.symbols.lookup(name)
            else:
                raise Exception('Frame has no variable %s' % name)

        if not isinstance(value, W_Reference):
            value = W_Reference(value)

        self._store(index, value)

    def get_reference(self, name, index=-1):
        if index < 0:
            if self.symbols.contains(name):
                index = self.symbols.lookup(name)
            else:
                raise Exception('Frame has no variable %s' % name)

        return self._load(index)

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


class FunctionFrame(Frame):
    def __init__(self, space, parent_frame, code, arguments=None):
        Frame.__init__(self, space, code)
        assert isinstance(parent_frame, Frame)

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
                if isinstance(argument, W_Reference):
                    argument = argument.get_value()
                # todo use copy.deepcopy for this
                argument = argument.__deepcopy__()
                argument = W_Reference(argument)
            else:
                if isinstance(argument, W_Reference):
                    pass
                else:
                    raise Exception("Was expecting a reference")
            # safe to set the reference by param_index because params
            # are the first variables in he vars list
            self.set_reference(param, param_index, argument)
            param_index += 1

        # every variable referenced in 'globals' needs to be initialized
        for name in code.globals():
            ref = parent_frame.get_reference(name)
            if ref is None:
                raise Exception("Global variable %s does not exist" % name)
            self.set_reference(name, -1, ref)

    def argv(self):
        return self.arguments
