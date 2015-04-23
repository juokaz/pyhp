from rpython.rlib.rsre.rsre_re import findall, sub as re_sub
from rpython.rlib.rstring import replace
from rpython.rlib.rarithmetic import ovfcheck
from rpython.rlib.objectmodel import specialize


class NativeFunction(object):
    def __init__(self, name, method):
        self.name = name
        self.method = method

    def call(self, arguments):
        return self.method(arguments)


class Property(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value


class W_Root(object):
    pass


class W_IntObject(W_Root):
    def __init__(self, intval):
        assert(isinstance(intval, int))
        self.intval = intval

    def to_number(self):
        return float(self.intval)

    def is_true(self):
        return self.intval != 0

    def str(self):
        return str(self.intval)

    def __repr__(self):
        return 'W_IntObject(%s)' % (self.intval,)


class W_FloatObject(W_Root):
    def __init__(self, floatval):
        assert(isinstance(floatval, float))
        self.floatval = floatval

    def to_number(self):
        return self.floatval

    def str(self):
        return str(self.floatval)

    def __repr__(self):
        return 'W_FloatObject(%s)' % (self.floatval,)


class W_StringObject(W_Root):
    def __init__(self, stringval):
        assert(isinstance(stringval, str))
        self.stringval = self.string_unquote(stringval)

        self.variables = []
        if not self.is_single_quoted(stringval):
            self.variables = self.extract_variables()

    def replace(self, search, replace_with):
        return W_StringObject(replace(self.stringval, search, replace_with))

    def get_variables(self):
        return self.variables

    def str(self):
        return str(self.stringval)

    def is_single_quoted(self, string):
        return string[0] == "'"

    def extract_variables(self):
        VARIABLENAME = "\$[a-zA-Z_][a-zA-Z0-9_]*"

        # array index regex matching the index and the brackets
        ARRAYINDEX = "\[(?:[0-9]+|" + VARIABLENAME + ")\]"

        # match variables and array access
        VARIABLE = "(" + VARIABLENAME + "(?:" + ARRAYINDEX + ")*)"
        CURLYVARIABLE = "{?" + VARIABLE + "}?"
        variables = findall(CURLYVARIABLE, self.stringval)

        # array index regex matching just the index
        ARRAYINDEX = "\[([0-9]+|" + VARIABLENAME + ")\]"

        variables_ = []
        # remove curly braces around variables
        for variable in variables:
            self.stringval = replace(self.stringval, '{' + variable + '}',
                                     variable)

            # is this an array access?
            indexes = findall(ARRAYINDEX, variable)
            identifier = re_sub(ARRAYINDEX, '', variable)

            variables_.append((variable, identifier, indexes))

        return variables_

    def string_unquote(self, string):
        # dont unquote if already unquoted
        if string[0] not in ["'", '"']:
            return string

        # XXX I don't think this works, it's very unlikely IMHO
        #     test it
        temp = []
        stop = len(string)-1
        # XXX proper error
        assert stop >= 0

        internalstring = string[1:stop]

        for c in internalstring:
            temp.append(c)
        return ''.join(temp)

    def len(self):
        return W_IntObject(len(self.stringval))

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
        try:
            return self.propdict[key].value
        except KeyError:
            return W_Null()

    def str(self):
        r = '['
        for key, element in self.propdict.iteritems():
            value = element.value.str()
            r += '%s: %s' % (key, value) + ', '
        r = r.strip(', ')
        r += ']'
        return r


class W_Boolean(W_Root):
    _immutable_fields_ = ['boolval']

    def __init__(self, boolval):
        assert(isinstance(boolval, bool))
        self.boolval = boolval

    def str(self):
        if self.boolval is True:
            return "true"
        return "false"


class W_Null(W_Root):
    def str(self):
        return "null"


def isint(w):
    return isinstance(w, W_IntObject)


def isstr(w):
    return isinstance(w, W_StringObject)


def isfloat(w):
    return isinstance(w, W_FloatObject)


def plus(left, right):
    if isstr(left) or isstr(right):
        sleft = left.str()
        sright = right.str()
        return W_StringObject(sleft + sright)
    # hot path
    if isint(left) and isint(right):
        ileft = left.intval
        iright = right.intval
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
        return W_IntObject(nleft.intval + constval)
    else:
        return plus(nleft, W_IntObject(constval))


def decrement(nleft, constval=1):
    if isint(nleft):
        return W_IntObject(nleft.intval - constval)
    else:
        return sub(nleft, W_IntObject(constval))


def sub(left, right):
    if isint(left) and isint(right):
        # XXX fff
        ileft = left.intval
        iright = right.intval
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
        ileft = left.intval
        iright = right.intval
        try:
            return W_IntObject(ovfcheck(ileft * iright))
        except OverflowError:
            return W_FloatObject(float(ileft) * float(iright))
    fleft = left.to_number()
    fright = right.to_number()
    return W_FloatObject(fleft * fright)


def division(left, right):
    if isint(left) and isint(right):
        # XXXX test & stuff
        ileft = left.intval
        iright = right.intval
        try:
            return W_IntObject(ovfcheck(ileft / iright))
        except OverflowError:
            return W_FloatObject(float(ileft) / float(iright))
    fleft = left.to_number()
    fright = right.to_number()
    return W_FloatObject(fleft / fright)


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
        return _compare(x.intval, y.intval)

    if isfloat(x) and isfloat(y):
        n1 = x.to_number()
        n2 = x.to_number()
        return _compare(n1, n2)


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
