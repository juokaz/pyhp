from rpython.rlib.rsre.rsre_re import findall
from rpython.rlib.rstring import replace
from rpython.rlib.rarithmetic import ovfcheck
from rpython.rlib.objectmodel import specialize
from constants import unescapedict

from rpython.rlib import jit

from pyhp.frame import Frame, VarMap


class Property(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value


class W_Root(object):
    _settled_ = True
    _immutable_fields_ = ['_type_']
    _type_ = ''

    def is_true(self):
        return False

    def str(self):
        return ''

    def len(self):
        return 0

    def replace(self, search, replace_with):
        pass

    def get_variables(self):
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


class W_StringObject(W_Root):
    _immutable_fields_ = ['stringval', 'variables[*]']

    def __init__(self, stringval):
        assert(isinstance(stringval, str))
        self.stringval = self.string_unquote(stringval)

        if not self.is_single_quoted(stringval):
            self.variables = self.extract_variables()
        else:
            self.variables = []

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

            identifier = variable
            for index in indexes:
                identifier = replace(identifier, '[' + index + ']', '')

            variables_.append((variable, identifier, indexes))

        return variables_

    def string_unquote(self, string):
        # dont unquote if already unquoted
        if string[0] not in ["'", '"']:
            return string

        temp = []
        stop = len(string)-1
        # XXX proper error
        assert stop >= 0
        last = ""

        internalstring = string[1:stop]

        for c in internalstring:
            if last == "\\":
                # Lookup escape sequence. Ignore the backslash for
                # unknown escape sequences (like SM)
                unescapeseq = unescapedict.get(last+c, c)
                temp.append(unescapeseq)
                c = ' '  # Could be anything
            elif c != "\\":
                temp.append(c)
            last = c
        return ''.join(temp)

    def len(self):
        return len(self.stringval)

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


class NativeFunction(W_Function):
    _immutable_fields_ = ['name', 'method']

    def __init__(self, name, method):
        self.name = name
        self.method = method

    def call(self, params, frame):
        return self.method(params)

    def __repr__(self):
        return 'NativeFunction(%s)' % (self.name,)


class W_ScriptFunction(W_Function):
    _immutable_fields_ = ['name', 'funcobj', 'scope', 'params[*]']

    def __init__(self, funcobj):
        self.name = funcobj.name
        self.funcobj = funcobj
        self.scope = funcobj.body.get_symbols()
        self.params = funcobj.body.params()

    @jit.unroll_safe
    def call(self, params, frame):
        func = self.get_funcobj()
        jit.promote(func)

        varmap = VarMap(self.scope, frame.varmap)

        # set call arguments as variable values
        param_index = 0
        for variable in self.params:
            index = varmap.get_index(variable)
            varmap.store(index, params[param_index])
            param_index += 1

        new_frame = Frame(varmap, frame.global_scope)
        return func.run(new_frame)

    def get_funcobj(self):
        return self.funcobj

    def __repr__(self):
        return 'ScriptFunction(%s)' % (self.name,)


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
        sleft = left.str()
        sright = right.str()
        return W_StringObject(sleft + sright)
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
