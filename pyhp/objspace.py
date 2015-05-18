from rpython.rlib.objectmodel import enforceargs
from rpython.rlib import jit

from pyhp.datatypes import W_Function, W_NativeFunction, W_Null, \
    W_Boolean, W_FloatObject, W_IntObject, W_StringObject, W_Root


class VersionTag(object):
    pass


# based on http://morepypy.blogspot.com/2011/03/controlling
# -tracing-of-interpreter-with_21.html
class NamesMap(object):
    def __init__(self):
        self.methods = {}
        self.version = VersionTag()

    def find(self, name):
        self = jit.hint(self, promote=True)
        version = jit.hint(self.version, promote=True)
        result = self._find_method(name, version)
        if result is not None:
            return result
        return None

    @jit.elidable
    def _find_method(self, name, version):
        return self.methods.get(name, None)

    def declare(self, name, value):
        self.methods[name] = value
        self.version = VersionTag()


class ObjectSpace(object):
    def __init__(self, global_functions):
        self.functions = NamesMap()
        self.constants = NamesMap()

        self._declare_global_functions(global_functions)

    def _declare_global_functions(self, functions):
        for func in functions:
            self.declare_function(func.name, func)

    def declare_function(self, name, func):
        assert isinstance(func, W_Function)
        self.functions.declare(name, func)

    def get_function(self, name):
        return self.functions.find(name)

    def declare_constant(self, name, value):
        assert isinstance(value, W_Root)
        self.constants.declare(name, value)

    def get_constant(self, name):
        return self.constants.find(name)


@enforceargs(int)
def newint(i):
    return W_IntObject(i)


@enforceargs(float)
def newfloat(f):
    return W_FloatObject(f)


@enforceargs(unicode)
def newstring(s):
    return W_StringObject(s)

w_Null = W_Null()
jit.promote(w_Null)
w_True = W_Boolean(True)
jit.promote(w_True)
w_False = W_Boolean(False)
jit.promote(w_False)


@enforceargs(bool)
def newbool(val):
    if val:
        return w_True
    return w_False


def new_native_function(name, function, params=[]):
    return W_NativeFunction(name, function)
