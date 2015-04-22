from rpython.rlib.rsre.rsre_re import findall
from rpython.rlib.rstring import replace


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

    def add(self, other):
        if not isinstance(other, W_IntObject):
            raise Exception("wrong type")
        return W_IntObject(self.intval + other.intval)

    def sub(self, other):
        if not isinstance(other, W_IntObject):
            raise Exception("wrong type")
        return W_IntObject(self.intval - other.intval)

    def incr(self, n=None):
        if isinstance(n, W_IntObject):
            self.intval += n.intval
        else:
            self.intval += 1
        return self

    def decr(self, n=None):
        if isinstance(n, W_IntObject):
            self.intval -= n.intval
        else:
            self.intval -= 1
        return self

    def lt(self, other):
        if not isinstance(other, W_IntObject):
            raise Exception("wrong type")
        return W_IntObject(self.intval < other.intval)

    def ge(self, other):
        if not isinstance(other, W_IntObject):
            raise Exception("wrong type")
        return W_IntObject(self.intval >= other.intval)

    def eq(self, other):
        if not isinstance(other, W_IntObject):
            raise Exception("wrong type")
        return W_IntObject(self.intval == other.intval)

    def is_true(self):
        return self.intval != 0

    def str(self):
        return str(self.intval)


class W_FloatObject(W_Root):
    def __init__(self, floatval):
        assert(isinstance(floatval, float))
        self.floatval = floatval

    def add(self, other):
        if not isinstance(other, W_FloatObject):
            raise Exception("wrong type")
        return W_FloatObject(self.floatval + other.floatval)

    def sub(self, other):
        if not isinstance(other, W_FloatObject):
            raise Exception("wrong type")
        return W_FloatObject(self.floatval - other.floatval)

    def lt(self, other):
        if not isinstance(other, W_FloatObject):
            raise Exception("wrong type")
        return W_IntObject(self.floatval < other.floatval)

    def ge(self, other):
        if not isinstance(other, W_FloatObject):
            raise Exception("wrong type")
        return W_IntObject(self.floatval >= other.floatval)

    def eq(self, other):
        if not isinstance(other, W_FloatObject):
            raise Exception("wrong type")
        return W_IntObject(self.floatval == other.floatval)

    def str(self):
        return str(self.floatval)


class W_StringObject(W_Root):
    def __init__(self, stringval):
        assert(isinstance(stringval, str))
        self.stringval = self.string_unquote(stringval)

        self.variables = []
        if not self.is_single_quoted(stringval):
            self.variables = self.extract_variables(self.stringval)

    def append(self, other):
        if not isinstance(other, W_StringObject):
            raise Exception("wrong type")
        return W_StringObject(self.stringval + other.stringval)

    def replace(self, search, replace_with):
        return W_StringObject(replace(self.stringval, search, replace_with))

    def get_variables(self):
        return self.variables

    def str(self):
        return str(self.stringval)

    def is_single_quoted(self, string):
        return string[0] == "'"

    def extract_variables(self, string):
        VARIABLENAME = "\$[a-zA-Z_][a-zA-Z0-9_]*"
        return findall(VARIABLENAME, string)

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
