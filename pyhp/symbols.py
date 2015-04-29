from rpython.rlib import jit


class Map(object):
    NOT_FOUND = -1
    _immutable_fields_ = ['index', 'back', 'name']

    def __init__(self):
        self.index = self.NOT_FOUND
        self.forward_pointers = {}
        self.back = None
        self.name = None

    def __repr__(self):
        return "%(back)s, [%(index)d]:%(name)s" % \
            {'back': repr(self.back), 'index': self.index, 'name': self.name}

    @jit.elidable_promote("0")
    def contains(self, name):
        idx = self.lookup(name)
        return self.not_found(idx) is False

    @jit.elidable_promote("0")
    def not_found(self, idx):
        return idx == self.NOT_FOUND

    @jit.elidable_promote("0")
    def lookup(self, name):
        node = self._find_node_with_name(name)
        if node is not None:
            return node.index
        return self.NOT_FOUND

    def _find_node_with_name(self, name):
        if self.name == name:
            return self
        if self.back is not None:
            return self.back._find_node_with_name(name)

    def _key(self):
        return (self.name)

    def empty(self):
        return True

    @jit.elidable
    def len(self):
        return self.index + 1

    @jit.elidable
    def add(self, name):
        assert self.lookup(name) == self.NOT_FOUND
        node = self.forward_pointers.get((name), None)
        if node is None:
            node = MapNode(self, name)
            self.forward_pointers[node._key()] = node
        return node


class MapRoot(Map):
    def __repr__(self):
        return "[%(index)d]:%(name)s" % {'index': self.index,
                                         'name': self.name}


class MapNode(Map):
    def __init__(self, back, name):
        Map.__init__(self)
        self.back = back
        self.name = name
        self.index = back.index + 1

    def empty(self):
        return False


ROOT_MAP = MapRoot()


def new_map():
    return ROOT_MAP
