from rpython.rlib.rstring import replace
from rpython.rlib.rstring import StringBuilder
from rpython.rlib.rStringIO import RStringIO
from rpython.rlib.rarithmetic import ovfcheck
from rpython.rlib.objectmodel import specialize
from constants import CURLYVARIABLE, ARRAYINDEX

from rpython.rlib import jit

from pyhp.frame import FunctionFrame
import math


class Property(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value


class W_Root(object):
    _settled_ = True

    def is_true(self):
        return False

    def str(self):
        return ''

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

    def to_list(self):
        pass

    def get_bytecode(self):
        pass


class W_Number(W_Root):
    def is_true(self):
        return self.to_number() != 0


class W_IntObject(W_Number):
    _immutable_fields_ = ['intval']

    def __init__(self, intval):
        assert(isinstance(intval, int))
        self.intval = intval

    def to_number(self):
        return float(self.intval)

    def get_int(self):
        return self.intval

    def str(self):
        return str(self.intval)

    def __repr__(self):
        return 'W_IntObject(%s)' % (self.intval,)


class W_FloatObject(W_Number):
    _immutable_fields_ = ['floatval']

    def __init__(self, floatval):
        assert(isinstance(floatval, float))
        self.floatval = floatval

    def to_number(self):
        return self.floatval

    def str(self):
        return str(self.floatval)

    def __repr__(self):
        return 'W_FloatObject(%s)' % (self.floatval,)


def string_unquote(string):
    s = string
    single_quotes = True
    if s.startswith('"'):
        assert s.endswith('"')
        single_quotes = False
    else:
        assert s.startswith("'")
        assert s.endswith("'")
    s = s[:-1]
    s = s[1:]

    if not single_quotes:
        variables_ = []
        variables = CURLYVARIABLE.findall(s)

        # remove curly braces around variables
        for variable in variables:
            s = replace(s, '{' + variable + '}', variable)

            # is this an array access?
            indexes = ARRAYINDEX.findall(variable)

            identifier = variable
            for index in indexes:
                identifier = replace(identifier, '[' + index + ']', '')

            variables_.append((variable, identifier, indexes))
    else:
        variables_ = []

    return s, variables_


def string_unescape(string):
    s = string
    size = len(string)

    if size == 0:
        return ''

    builder = StringBuilder(size)
    pos = 0
    while pos < size:
        ch = s[pos]

        # Non-escape characters are interpreted as Unicode ordinals
        if ch != '\\':
            builder.append(ch)
            pos += 1
            continue

        # - Escapes
        pos += 1
        if pos >= size:
            message = "\\ at end of string"
            raise Exception(message)

        ch = s[pos]
        pos += 1
        # \x escapes
        if ch == '\n':
            pass
        elif ch == '\\':
            builder.append('\\')
        elif ch == '\'':
            builder.append('\'')
        elif ch == '\"':
            builder.append('\"')
        elif ch == 'b':
            builder.append('\b')
        elif ch == 'f':
            builder.append('\f')
        elif ch == 't':
            builder.append('\t')
        elif ch == 'n':
            builder.append('\n')
        elif ch == 'r':
            builder.append('\r')
        elif ch == 'v':
            builder.append('\v')
        elif ch == 'a':
            builder.append('\a')
        else:
            builder.append(ch)

    return builder.build()


class W_StringObject(W_Root):
    _immutable_fields_ = ['stringval']

    def __init__(self, stringval):
        assert(isinstance(stringval, str))
        self.stringval = RStringIO()
        self.stringval.write(stringval)

    def append(self, stringval):
        self.stringval.write(stringval)

    def str(self):
        return self.stringval.getvalue()

    def len(self):
        return len(self.str())

    def __repr__(self):
        return 'W_StringObject(%s)' % (self.stringval,)


class W_Array(W_Root):
    def __init__(self):
        self.propdict = {}

    def put(self, key, value):
        assert(isinstance(key, str))
        if key not in self.propdict:
            self.propdict[key] = Property(key, value)
        else:
            self.propdict[key].value = value

    def get(self, key):
        assert(isinstance(key, str))
        return self.propdict[key].value

    def str(self):
        r = '['
        for key, element in self.propdict.iteritems():
            value = element.value.str()
            r += '%s: %s' % (key, value) + ', '
        r = r.strip(', ')
        r += ']'
        return r

    def __repr__(self):
        return 'W_Array(%s)' % (self.str(),)


class W_List(W_Root):
    _immutable_fields_ = ['values[*]']

    def __init__(self, values):
        self.values = values

    def to_list(self):
        return self.values

    def __str__(self):
        return 'W_List(%s)' % (str([str(v) for v in self.values]))


class W_Boolean(W_Root):
    _immutable_fields_ = ['boolval']

    def __init__(self, boolval):
        assert(isinstance(boolval, bool))
        self.boolval = boolval

    def str(self):
        if self.boolval is True:
            return "true"
        return "false"

    def is_true(self):
        return self.boolval


class W_Null(W_Root):
    def str(self):
        return "null"


class W_Function(W_Root):
    pass


class W_CodeFunction(W_Function):
    _immutable_fields_ = ['name', 'funcobj', 'varmap']

    def __init__(self, funcobj, varmap=None):
        self.name = funcobj.name()
        self.funcobj = funcobj
        self.varmap = varmap

    def call(self, params, frame):
        func = self.get_funcobj()
        jit.promote(func)

        new_frame = FunctionFrame(func, params, self.varmap)
        return func.run(new_frame)

    def get_funcobj(self):
        return self.funcobj

    def __repr__(self):
        return 'W_CodeFunction(%s)' % (self.name,)


def isint(w):
    return isinstance(w, W_IntObject)


def isstr(w):
    return isinstance(w, W_StringObject)


def isfloat(w):
    return isinstance(w, W_FloatObject)


def isnumber(w):
    return isinstance(w, W_Number)


def plus(left, right):
    if isstr(left) or isstr(right):
        sright = right.str()
        left.append(sright)
        return left
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


def increment(nleft, constval=1):
    if isint(nleft):
        return W_IntObject(nleft.get_int() + constval)
    else:
        return plus(nleft, W_IntObject(constval))


def decrement(nleft, constval=1):
    if isint(nleft):
        return W_IntObject(nleft.get_int() - constval)
    else:
        return sub(nleft, W_IntObject(constval))


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


def division(left, right):
    fleft = left.to_number()
    fright = right.to_number()
    result = fleft / fright
    if int(result) == result:
        return W_IntObject(int(result))
    else:
        return W_FloatObject(result)


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
        n2 = x.to_number()
        return _compare(n1, n2)

    raise Exception('Incompatible types for comparison: %s %s' % (x, y))


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
