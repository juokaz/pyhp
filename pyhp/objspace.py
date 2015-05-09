from rpython.rlib.objectmodel import enforceargs
from rpython.rlib import jit

from pyhp.functions import NativeFunction
from pyhp.datatypes import W_CodeFunction, W_Null, W_Boolean, W_FloatObject, \
    W_IntObject, W_StringObject


class ObjectSpace(object):
    def __init__(self, global_functions):
        self.functions = {}
        self.constants = {}

        self._declare_global_functions(global_functions)

    def _declare_global_functions(self, functions):
        for func in functions:
            self.declare_function(func.name, func)

    def declare_function(self, name, func):
        assert isinstance(name, str)
        assert isinstance(func, W_CodeFunction)
        if name in self.functions:
            return False
        self.functions[name] = func
        return True

    def get_function(self, name):
        assert isinstance(name, str)
        return self.functions.get(name, None)

    def declare_constant(self, name, value):
        assert isinstance(name, str)
        if name in self.constants:
            return False
        self.constants[name] = value
        return True

    def get_constant(self, name):
        assert isinstance(name, str)
        return self.constants.get(name, None)


@enforceargs(int)
def newint(i):
    return W_IntObject(i)


@enforceargs(float)
def newfloat(f):
    return W_FloatObject(f)


@enforceargs(str)
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
    func = NativeFunction(name, function)
    obj = W_CodeFunction(func)
    return obj
