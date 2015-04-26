from rpython.rlib import jit

class VarMap(object):
    _immutable_fields_ = ['vars[*]', 'scope', 'parent']

    def __init__(self, scope, parent=None):
        self.scope = scope
        self.vars = [None] * len(scope)
        if parent is not None and parent.parent is not None:
            parent = parent.parent
        self.parent = parent

    def store(self, index, value):
        assert index >= 0
        self.vars[index] = value

    def load(self, index):
        assert index >= 0
        return self.vars[index]

    def get_index(self, name):
        return self.get_scope().get_index(name)

    def get_scope(self):
        return self.scope

    def get_parent(self):
        return self.parent

    def get_owning(self, name):
        try:
            if self.get_scope().has_global(name):
                return self.get_parent().get_owning(name)

            if self.get_scope().has_variable(name) or self.get_scope().has_function(name):
                return self

            return self.get_parent().get_owning(name)
        except AttributeError:
            return None


class Frame(object):
    _settled_ = True
    _immutable_fields_ = ['parent_frame', 'global_scope', 'scope', 'varmap']
    _virtualizable_ = ['valuestack[*]', 'valuestack_pos']

    def __init__(self, varmap, global_scope=None):
        self = jit.hint(self, access_directly=True, fresh_virtualizable=True)
        self.valuestack = [None] * 10  # safe estimate!
        self.varmap = varmap
        self.valuestack_pos = 0

        self.global_scope = global_scope

    def get_var(self, name, index=-1):
        if index < 0:
            index = self.get_index(name)

        try:
            varmap = self.get_owning(name)

            # if current frame has the variable defined
            return varmap.load(index)
        except AttributeError:
             # or it might be a global function
            if self.global_scope.has_identifier(name):
                return self.global_scope.get(name)

        return None

    def set_var(self, index, name, value):
        assert index >= 0

        varmap = self.get_owning(name)
        varmap.store(index, value)

    @jit.elidable_promote("0")
    def get_owning(self, name):
        return self.varmap.get_owning(name)

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

    def top(self):
        pos = self.get_pos() - 1
        assert pos >= 0
        return self.valuestack[pos]

    def get_pos(self):
        return jit.promote(self.valuestack_pos)

    def __repr__(self):
        return "Frame %s" % (self.varmap)
