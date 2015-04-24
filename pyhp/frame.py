from rpython.rlib import jit


class Frame(object):
    _settled_ = True
    _immutable_fields_ = ['parent_frame', 'global_scope', 'scope', 'vars[*]']
    _virtualizable_ = ['valuestack[*]', 'valuestack_pos']

    def __init__(self, scope, parent_frame=None, global_scope=None):
        self = jit.hint(self, access_directly=True, fresh_virtualizable=True)
        self.valuestack = [None] * 50  # safe estimate!
        self.vars = [None] * len(scope)
        self.valuestack_pos = 0

        self.scope = scope
        self.global_scope = global_scope
        self.parent_frame = parent_frame

    def create_new_frame(self, scope):
        if self.parent_frame is not None:
            parent_frame = self.parent_frame
        else:
            parent_frame = self

        return Frame(scope, parent_frame, self.global_scope)

    def get_var(self, index, name):
        assert index >= 0

        # if current frame has the variable defined
        variable = self.vars[index]

        if variable is not None:
            return variable

        is_function = name[0] != '$'

        if is_function:
            # if it's a function it might be defined in the parent frame
            if self.parent_frame:
                variable = self.parent_frame.get_var(index, name)
                if variable:
                    return variable

            # or it might be a global function
            if self.global_scope.has_identifier(name):
                return self.global_scope.get(name)
        else:
            # a variable can be global
            if name in self.scope.globals:
                return self.parent_frame.get_var(index, name)

        return None

    def get_variable_frame(self, name):
        if name in self.scope.globals:
            return self.parent_frame.get_variable_frame(name)

        if name in self.scope.variables or self.scope.functions:
            return self

        raise Exception("Identifier %s not found in any frame" % name)

    def set_var(self, index, name, value):
        assert index >= 0

        frame = self.get_variable_frame(name)
        frame.vars[index] = value

    def push(self, v):
        pos = jit.hint(self.valuestack_pos, promote=True)

        # prevent stack overflow
        len_stack = len(self.valuestack)
        assert pos >= 0 and len_stack > pos

        self.valuestack[pos] = v
        self.valuestack_pos = pos + 1

    def pop(self):
        pos = jit.hint(self.valuestack_pos, promote=True)
        new_pos = pos - 1
        assert new_pos >= 0
        v = self.valuestack[new_pos]
        self.valuestack_pos = new_pos
        return v

    def top(self):
        pos = self.valuestack_pos - 1
        assert pos >= 0
        return self.valuestack[pos]

    def __repr__(self):
        return "Frame %s, parent %s" % (self.vars, self.parent_frame)
