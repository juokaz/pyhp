from rpython.rlib.objectmodel import enforceargs, specialize
from rpython.rlib import jit

from pyhp.datatypes import W_Function, W_NativeFunction, \
    W_FloatObject, W_IntObject, W_StringObject, W_Root, W_DictArray, \
    W_ListArray, w_Null, w_True, w_False


class VersionTag(object):
    pass


# based on http://morepypy.blogspot.com/2011/03/controlling
# -tracing-of-interpreter-with_21.html
class NamesMap(object):
    def __init__(self, initdict={}):
        self.methods = initdict
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
    w_Null = w_Null
    w_True = w_True
    w_False = w_False

    def __init__(self, global_functions):
        self.functions = NamesMap(global_functions.copy())
        self.constants = NamesMap()

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

    @specialize.argtype(1)
    def wrap(self, value):
        if value is None:
            return self.w_Null
        elif isinstance(value, W_Root):
            return value
        elif isinstance(value, bool):
            return newbool(value)
        elif isinstance(value, int):
            return newint(value)
        elif isinstance(value, float):
            return newfloat(value)
        elif isinstance(value, unicode):
            return newstring(value)
        elif isinstance(value, str):
            u_str = unicode(value)
            return newstring(u_str)
        elif isinstance(value, list):
            return newlistarray(value)

        raise TypeError("ffffuuu %s" % value)

    def newdictarray(self, value):
        return newdictarray(value)


@enforceargs(int)
def newint(i):
    return W_IntObject(i)


@enforceargs(float)
def newfloat(f):
    return W_FloatObject(f)


@enforceargs(unicode)
def newstring(s):
    return W_StringObject(s)


@enforceargs(bool)
def newbool(val):
    if val:
        return w_True
    return w_False


def newlistarray(val):
    return W_ListArray(val)


def newdictarray(val):
    return W_DictArray(val)


def new_native_function(name, function, params=[]):
    return W_NativeFunction(name, function, params)
