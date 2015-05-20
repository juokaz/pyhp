from rpython.rlib.rstring import UnicodeBuilder
from rpython.rlib.rarithmetic import ovfcheck
from rpython.rlib.objectmodel import specialize, instantiate
from rpython.rlib.rarithmetic import intmask
from collections import OrderedDict

from rpython.rlib import jit

import math


class W_Root(object):
    _settled_ = True

    def is_true(self):
        return False

    def str(self):
        return u''

    def str_full(self):
        return self.str()

    def len(self):
        return 0

    def append(self, stringval):
        pass

    def to_number(self):
        return 0.0

    def get_int(self):
        return 0

    def put(self, key, value):
        pass

    def get(self, key):
        pass

    def to_iterator(self):
        return None

    def empty(self):
        return False

    def set_value(self, value):
        pass

    def get_value(self):
        return self

    def __deepcopy__(self):
        obj = instantiate(self.__class__)
        return obj


class W_Reference(W_Root):
    def __init__(self, value):
        self.value = value

    def get_value(self):
        return self.value

    def put_value(self, value):
        self.value = value
        return self

    def __repr__(self):
        return 'W_Reference(%s)' % (self.value,)


class W_Number(W_Root):
    def is_true(self):
        return self.to_number() != 0


class W_IntObject(W_Number):
    _immutable_fields_ = ['intval']

    def __init__(self, intval):
        self.intval = intmask(intval)

    def to_number(self):
        return float(self.intval)

    def get_int(self):
        return self.intval

    def str(self):
        return u"%d" % self.intval

    def __deepcopy__(self):
        obj = instantiate(self.__class__)
        obj.intval = self.intval
        return obj

    def __repr__(self):
        return 'W_IntObject(%s)' % (self.intval,)


class W_FloatObject(W_Number):
    _immutable_fields_ = ['floatval']

    def __init__(self, floatval):
        self.floatval = floatval

    def to_number(self):
        return self.floatval

    def str(self):
        return unicode(str(self.floatval))

    def __deepcopy__(self):
        obj = instantiate(self.__class__)
        obj.floatval = self.floatval
        return obj

    def __repr__(self):
        return 'W_FloatObject(%s)' % (self.floatval,)


class W_StringObject(W_Root):
    _immutable_fields_ = ['stringval']

    def __init__(self, stringval):
        assert stringval is not None
        assert isinstance(stringval, unicode)
        self.stringval = stringval

    def append(self, stringval):
        builder = UnicodeBuilder()
        concat = W_ConcatStringObject(builder)
        concat.builder.append(self.stringval)
        concat.builder.append(stringval)
        return concat

    def get(self, key):
        assert isinstance(key, W_IntObject)
        key = key.get_int()
        return W_StringObject(self.stringval[key])

    def str(self):
        return self.stringval

    def len(self):
        return len(self.stringval)

    def __deepcopy__(self):
        obj = instantiate(self.__class__)
        obj.stringval = self.stringval  # todo this is incorrect
        return obj

    def __repr__(self):
        return 'W_StringObject(%s)' % (self.str(),)


class W_ConcatStringObject(W_StringObject):
    _immutable_fields_ = ['builder']

    def __init__(self, builder):
        self.builder = builder

    def append(self, stringval):
        builder = self.builder
        concat = W_ConcatStringObject(builder)
        concat.builder.append(stringval)
        return concat

    def get(self, key):
        key = key.get_int()
        return W_StringObject(self.str()[key])

    def str(self):
        return self.builder.build()

    def len(self):
        return len(self.str())


class W_StringSubstitution(W_Root):
    _immutable_fields_ = ['strings[:]']

    def __init__(self, strings):
        self.strings = strings

    def __repr__(self):
        return 'W_StringSubstitution(%s)' % (self.strings,)


class W_Array(W_Root):
    pass


class W_ListArray(W_Array):
    def __init__(self, items=[]):
        self.data = items

    def len(self):
        return len(self.data)

    def put(self, key, value):
        if isinstance(key, W_IntObject):
            index = key.get_int()
            length = self.len()
            if index >= length:
                self.data += [None] * (index - length + 1)
                self.data[index] = value

            self.data[index] = value
            return self
        else:
            array = self.to_dict()
            array.put(key, value)
            return array

    def get(self, key):
        if not isinstance(key, W_IntObject):
            raise Exception("key %s not in %s" % (key, self))
        try:
            element = self.data[key.get_int()]
            return element
        except KeyError:
            raise Exception("key %s not in %s" % (key, self))

    def str(self):
        return u'Array'

    @jit.unroll_safe
    def str_full(self):
        result = u"Array\n" + u"(\n"
        for key, value in enumerate(self.data):
            lines = value.str_full().split(u"\n")
            string = lines[0]
            end = len(lines)-1
            if end > 1:
                offset = u"\n".join([u"\t" + line for line in lines[1:end]])
                string = string + u"\n" + offset
            result += u"\t[" + unicode(str(key)) + u"] => " + string + u"\n"
        result += u")\n"
        return result

    def to_iterator(self):
        array = self.to_dict()
        iterator = W_Iterator(array)
        return iterator

    @jit.unroll_safe
    def to_dict(self):
        array = OrderedDict()
        for key, value in enumerate(self.data):
            array[unicode(str(key))] = value
        return W_DictArray(array)

    def __deepcopy__(self):
        obj = instantiate(self.__class__)
        obj.data = self.data[:]
        return obj

    def __repr__(self):
        return 'W_ListArray(%s)' % (self.str_full(),)


class W_DictArray(W_Array):
    def __init__(self, items={}):
        self.data = items

    def len(self):
        return len(self.data)

    def put(self, key, value):
        _key = key.str()
        self.data[_key] = value
        return self

    def get(self, key):
        _key = key.str()
        try:
            element = self.data[_key]
            return element
        except KeyError:
            raise Exception("key %s not in %s" % (key, self))

    def str(self):
        return u'Array'

    @jit.unroll_safe
    def str_full(self):
        result = u"Array\n" + u"(\n"
        for key, value in self.data.iteritems():
            lines = value.str_full().split(u"\n")
            string = lines[0]
            end = len(lines)-1
            if end > 1:
                offset = u"\n".join([u"\t" + line for line in lines[1:end]])
                string = string + u"\n" + offset
            result += u"\t[" + key + u"] => " + string + u"\n"
        result += u")\n"
        return result

    @jit.unroll_safe
    def to_iterator(self):
        iterator = W_Iterator(self)
        return iterator

    def __deepcopy__(self):
        obj = instantiate(self.__class__)
        obj.data = self.data.copy()
        return obj

    def __repr__(self):
        return 'W_DictArray(%s)' % (self.str_full(),)


class W_Iterator(W_Root):
    _immutable_fields_ = ['array']

    def __init__(self, array):
        self.array = array
        self.keys = array.data.keys()
        self.index = 0
        self.end = array.len()

    def _current(self):
        try:
            return self.keys[self.index]
        except IndexError:
            return u'-1'

    def current(self):
        key = self._current()
        return self.array.data[key]

    def key(self):
        return W_StringObject(self._current())

    def next(self):
        value = self.current()
        self.index += 1
        return value

    def empty(self):
        return self.index == self.end

    def to_string(self):
        return 'W_Iterator(%s)' % (str([str(v) for v in self.values]))


class W_Boolean(W_Root):
    _immutable_fields_ = ['boolval']

    def __init__(self, boolval):
        self.boolval = boolval

    def str(self):
        if self.boolval is True:
            return u"true"
        return u"false"

    def __deepcopy__(self):
        obj = instantiate(self.__class__)
        obj.boolval = self.boolval
        return obj

    def is_true(self):
        return self.boolval


class W_Null(W_Root):
    def str(self):
        return u"null"


class W_Function(W_Root):
    pass


class W_CodeFunction(W_Function):
    _immutable_fields_ = ['name', 'bytecode', 'globals[*]', 'parameters[*]']

    def __init__(self, bytecode):
        self.name = bytecode.name
        self.bytecode = bytecode
        self.globals = bytecode.globals()
        self.parameters = bytecode.params()

    @jit.unroll_safe
    def call(self, interpreter, space, frame, params):
        bytecode = self.bytecode

        from pyhp.frame import Frame
        new_frame = Frame(interpreter, bytecode)

        # set call arguments as variable values
        param_index = 0
        for param, by_value in self.parameters:
            argument = params[param_index]
            if by_value:
                if isinstance(argument, W_Reference):
                    argument = argument.get_value()
                # todo use copy.deepcopy for this
                argument = argument.__deepcopy__()
            else:
                if isinstance(argument, W_Reference):
                    pass
                else:
                    raise Exception("Was expecting a reference")
            # safe to set the reference by param_index because params
            # are the first variables in he vars list
            new_frame.store_variable(param, param_index, argument)
            param_index += 1

        # every variable referenced in 'globals' needs to be initialized
        for name, index in self.globals:
            ref = frame.get_reference_by_name(name)
            if ref is None:
                raise Exception("Global variable %s does not exist" % name)
            new_frame.set_reference(name, index, ref)

        result = interpreter.execute(bytecode, new_frame)

        assert result is not None
        return result

    def __repr__(self):
        return 'W_CodeFunction(%s)' % (self.name,)


class W_NativeFunction(W_Function):
    _immutable_fields_ = ['name', 'function', 'parameters[*]']

    def __init__(self, name, function, parameters):
        self.name = name
        self.function = function
        self.parameters = parameters

    def call(self, interpreter, space, frame, params):
        result = self.function(interpreter, space, params)

        assert result is not None
        return result

    def __repr__(self):
        return 'W_NativeFunction(%s)' % (self.name,)


def isint(w):
    return isinstance(w, W_IntObject)


def isstr(w):
    return isinstance(w, W_StringObject)


def isfloat(w):
    return isinstance(w, W_FloatObject)


def isnumber(w):
    return isinstance(w, W_Number)


@specialize.argtype(0, 1)
def plus(left, right):
    if isstr(left) or isstr(right):
        sright = right.str()
        return left.append(sright)
    # hot path
    if isint(left) and isint(right):
        ileft = left.get_int()
        iright = right.get_int()
        try:
            return W_IntObject(ovfcheck(ileft + iright))
        except OverflowError:
            return W_FloatObject(float(ileft) + float(iright))
    else:
        fleft = left.to_number()
        fright = right.to_number()
        return W_FloatObject(fleft + fright)


@specialize.argtype(0)
def increment(nleft, constval=1):
    if isint(nleft):
        return W_IntObject(nleft.get_int() + constval)
    else:
        return plus(nleft, W_IntObject(constval))


@specialize.argtype(0)
def decrement(nleft, constval=1):
    if isint(nleft):
        return W_IntObject(nleft.get_int() - constval)
    else:
        return sub(nleft, W_IntObject(constval))


@specialize.argtype(0, 1)
def sub(left, right):
    if isint(left) and isint(right):
        # XXX fff
        ileft = left.get_int()
        iright = right.get_int()
        try:
            return W_IntObject(ovfcheck(ileft - iright))
        except OverflowError:
            return W_FloatObject(float(ileft) - float(iright))
    fleft = left.to_number()
    fright = right.to_number()
    return W_FloatObject(fleft - fright)


@specialize.argtype(0, 1)
def mult(left, right):
    if isint(left) and isint(right):
        # XXXX test & stuff
        ileft = left.get_int()
        iright = right.get_int()
        try:
            return W_IntObject(ovfcheck(ileft * iright))
        except OverflowError:
            return W_FloatObject(float(ileft) * float(iright))
    fleft = left.to_number()
    fright = right.to_number()
    return W_FloatObject(fleft * fright)


@specialize.argtype(0, 1)
def division(left, right):
    fleft = left.to_number()
    fright = right.to_number()
    result = fleft / fright
    if int(result) == result:
        return W_IntObject(int(result))
    else:
        return W_FloatObject(result)


@specialize.argtype(0, 1)
def mod(left, right):
    fleft = left.get_int()
    fright = right.get_int()

    if fleft == 0:
        return left

    return W_IntObject(int(math.fmod(fleft, fright)))


@specialize.argtype(0, 1)
def _compare_gt(x, y):
    return x > y


@specialize.argtype(0, 1)
def _compare_ge(x, y):
    return x >= y


@specialize.argtype(0, 1)
def _compare_eq(x, y):
    return x == y


def _base_compare(x, y, _compare):
    if isint(x) and isint(y):
        return _compare(x.get_int(), y.get_int())

    if isnumber(x) and isnumber(y):
        n1 = x.to_number()
        n2 = y.to_number()
        return _compare(n1, n2)

    s1 = x.str()
    s2 = y.str()
    return _compare(s1, s2)


def compare_gt(x, y):
    return _base_compare(x, y, _compare_gt)


def compare_ge(x, y):
    return _base_compare(x, y, _compare_ge)


def compare_lt(x, y):
    return _base_compare(y, x, _compare_gt)


def compare_le(x, y):
    return _base_compare(y, x, _compare_ge)


def compare_eq(x, y):
    return _base_compare(y, x, _compare_eq)

w_Null = W_Null()
jit.promote(w_Null)
w_True = W_Boolean(True)
jit.promote(w_True)
w_False = W_Boolean(False)
jit.promote(w_False)
