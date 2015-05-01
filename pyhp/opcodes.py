from pyhp.datatypes import W_IntObject, W_StringObject, \
    W_Null, W_Array, W_List, W_Boolean, W_FloatObject, W_Function, \
    W_CodeFunction, W_Iterator
from pyhp.datatypes import compare_gt, compare_ge, compare_lt, compare_le, \
    compare_eq
from pyhp.datatypes import plus, increment, decrement, sub, mult, division, mod

from pyhp.utils import printf

from rpython.rlib.rstring import replace

from rpython.rlib import jit


class Opcode(object):
    _settled_ = True

    def __init__(self):
        pass

    def get_name(self):
        return self.__class__.__name__

    def eval(self, frame):
        """ Execute in frame
        """
        raise NotImplementedError(self.get_name() + ".eval")

    def __str__(self):
        return self.get_name()


class LOAD_CONSTANT(Opcode):
    pass


class LOAD_VAR(Opcode):
    _immutable_fields_ = ['index', 'name']

    def __init__(self, index, name):
        self.index = index
        self.name = name

    def eval(self, frame):
        ref = frame.get_reference(self.name, self.index)
        variable = ref.get_value(self.name)
        if variable is None:
            raise Exception("Variable %s (%s) is not set" %
                            (self.index, self.name))
        frame.push(variable)

    def __str__(self):
        return 'LOAD_VAR %s, %s' % (self.index, self.name)


class LOAD_FUNCTION(Opcode):
    _immutable_fields_ = ['function']

    def __init__(self, function):
        self.function = function

    def eval(self, frame):
        frame.push(W_CodeFunction(self.function, frame.varmap))


class LOAD_LIST(Opcode):
    _immutable_fields_ = ['number']

    def __init__(self, number):
        self.number = number

    def eval(self, frame):
        list_w = frame.pop_n(self.number)
        frame.push(W_List(list_w))

    def __str__(self):
        return 'LOAD_LIST %d' % self.number


class LOAD_UNDEFINED(Opcode):
    def eval(self, frame):
        frame.push(W_Null())

    def __str__(self):
        return 'LOAD_UNDEFINED'


class LOAD_NULL(Opcode):
    def eval(self, frame):
        frame.push(W_Null())

    def __str__(self):
        return 'LOAD_NULL'


class LOAD_BOOLEAN(Opcode):
    _immutable_fields_ = ['value']

    def __init__(self, value):
        self.value = W_Boolean(value)

    def eval(self, frame):
        frame.push(self.value)

    def __str__(self):
        return 'LOAD_BOOLEAN %s' % (self.value)


class LOAD_INTVAL(Opcode):
    _immutable_fields_ = ['value']

    def __init__(self, value):
        self.value = W_IntObject(value)

    def eval(self, frame):
        frame.push(self.value)

    def __str__(self):
        return 'LOAD_INTVAL %s' % (self.value)


class LOAD_FLOATVAL(Opcode):
    _immutable_fields_ = ['value']

    def __init__(self, value):
        self.value = W_FloatObject(value)

    def eval(self, frame):
        frame.push(self.value)

    def __str__(self):
        return 'LOAD_FLOATVAL %s' % (self.value)


class LOAD_STRINGVAL(Opcode):
    _immutable_fields_ = ['value', 'variables[*]']

    def __init__(self, value, variables):
        assert isinstance(value, str)
        self.value = value
        self.variables = variables

    @jit.unroll_safe
    def eval(self, frame):
        stringval = self.value
        for variable in self.variables:
            search, identifier, indexes = variable
            ref = frame.get_reference(identifier)
            value = ref.get_value(identifier)
            for key in indexes:
                if key[0] == '$':
                    ref = frame.get_reference(key)
                    key = ref.get_value(key)
                elif str(int(key)) == key:
                    key = W_IntObject(int(key))
                else:
                    key = W_StringObject(key)
                value = value.get(key)
            replace_with = value.str()
            stringval = replace(stringval, search, replace_with)

        frame.push(W_StringObject(stringval))

    def __str__(self):
        return 'LOAD_STRINGVAL %s' % (self.value)


class LOAD_ARRAY(Opcode):
    _immutable_fields_ = ['number']

    def __init__(self, number):
        self.number = number

    @jit.unroll_safe
    def eval(self, frame):
        array = W_Array()
        list_w = frame.pop_n(self.number)
        for index, el in enumerate(list_w):
            array.put(W_IntObject(index), el)
        frame.push(array)

    def __str__(self):
        return 'LOAD_ARRAY %d' % (self.number)


class LOAD_MEMBER(Opcode):
    def eval(self, frame):
        array = frame.pop()
        member = frame.pop()
        value = array.get(member)
        frame.push(value)


class STORE_MEMBER(Opcode):
    def eval(self, frame):
        array = frame.pop()
        index = frame.pop()
        value = frame.pop()
        array.put(index, value)

        frame.push(array)

    def __str__(self):
        return 'STORE_MEMBER'


class ASSIGN(Opcode):
    _immutable_fields_ = ['index', 'name']

    def __init__(self, index, name):
        self.index = index
        self.name = name

    def eval(self, frame):
        value = frame.pop()
        ref = frame.get_reference(self.name, self.index)
        ref.put_value(value, self.name)

        frame.push(value)

    def __str__(self):
        return 'ASSIGN %s, %s' % (self.index, self.name)


class DISCARD_TOP(Opcode):
    def eval(self, frame):
        frame.pop()


class DUP(Opcode):
    def eval(self, frame):
        frame.push(frame.top())


class LABEL(Opcode):
    _immutable_fields_ = ['num']

    def __init__(self, num):
        self.num = num

    def __str__(self):
        return 'LABEL %d' % (self.num)


class BaseJump(Opcode):
    _immutable_fields_ = ['where']

    def __init__(self, where):
        self.where = where

    def eval(self, frame):
        pass


class JUMP_IF_FALSE(BaseJump):
    def do_jump(self, frame, pos):
        value = frame.pop()
        if not value.is_true():
            return self.where
        return pos + 1

    def __str__(self):
        return 'JUMP_IF_FALSE %d' % (self.where)


class JUMP_IF_FALSE_NOPOP(BaseJump):
    def do_jump(self, frame, pos):
        value = frame.top()
        if not value.is_true():
            return self.where
        frame.pop()
        return pos + 1

    def __str__(self):
        return 'JUMP_IF_FALSE_NOPOP %d' % (self.where)


class JUMP_IF_TRUE_NOPOP(BaseJump):
    def do_jump(self, frame, pos):
        value = frame.top()
        if value.is_true():
            return self.where
        frame.pop()
        return pos + 1

    def __str__(self):
        return 'JUMP_IF_TRUE_NOPOP %d' % (self.where)


class JUMP(BaseJump):
    def do_jump(self, frame, pos):
        return self.where

    def __str__(self):
        return 'JUMP %d' % (self.where)


class LOAD_ITERATOR(Opcode):
    def eval(self, frame):
        obj = frame.pop()
        iterator = obj.to_iterator()

        frame.push(iterator)


class JUMP_IF_ITERATOR_EMPTY(BaseJump):
    def do_jump(self, frame, pos):
        last_block_value = frame.pop()
        iterator = frame.top()
        if iterator.empty():
            # discard the iterator
            frame.pop()
            # put the last block value on the stack
            frame.push(last_block_value)
            return self.where
        return pos + 1

    def __str__(self):
        return 'JUMP_IF_ITERATOR_EMPTY %d' % (self.where)


class NEXT_ITERATOR(Opcode):
    def eval(self, frame):
        iterator = frame.top()
        assert isinstance(iterator, W_Iterator)
        key, value = iterator.next()
        frame.push(value)
        frame.push(key)


class RETURN(Opcode):
    def eval(self, frame):
        return frame.pop()


class PRINT(Opcode):
    def eval(self, frame):
        item = frame.top()
        printf(item.str())


class CALL(Opcode):
    def eval(self, frame):
        method = frame.pop()
        params = frame.pop()

        assert isinstance(method, W_Function)
        assert isinstance(params, W_List)

        res = method.call(params.to_list(), frame)
        frame.push(res)


class BaseDecision(Opcode):
    def eval(self, frame):
        right = frame.pop()
        left = frame.pop()
        res = self.decision(left, right)
        frame.push(W_Boolean(res))

    def decision(self, op1, op2):
        raise NotImplementedError


class EQ(BaseDecision):
    def decision(self, left, right):
        return compare_eq(left, right)


class GT(BaseDecision):
    def decision(self, left, right):
        return compare_gt(left, right)


class GE(BaseDecision):
    def decision(self, left, right):
        return compare_ge(left, right)


class LT(BaseDecision):
    def decision(self, left, right):
        return compare_lt(left, right)


class LE(BaseDecision):
    def decision(self, left, right):
        return compare_le(left, right)


class ADD(Opcode):
    def eval(self, frame):
        right = frame.pop()
        left = frame.pop()
        frame.push(plus(left, right))


class SUB(Opcode):
    def eval(self, frame):
        right = frame.pop()
        left = frame.pop()
        frame.push(sub(left, right))


class MUL(Opcode):
    def eval(self, frame):
        right = frame.pop()
        left = frame.pop()
        frame.push(mult(left, right))


class DIV(Opcode):
    def eval(self, frame):
        right = frame.pop()
        left = frame.pop()
        frame.push(division(left, right))


class MOD(Opcode):
    def eval(self, frame):
        right = frame.pop()
        left = frame.pop()
        frame.push(mod(left, right))


class BaseUnaryOperation(Opcode):
    pass


class NOT(BaseUnaryOperation):
    def eval(self, frame):
        val = frame.pop()
        boolval = val.is_true()
        frame.push(W_Boolean(not boolval))


class INCR(BaseUnaryOperation):
    def eval(self, frame):
        left = frame.pop()
        frame.push(increment(left))


class DECR(BaseUnaryOperation):
    def eval(self, frame):
        left = frame.pop()
        frame.push(decrement(left))


class COMMA(BaseUnaryOperation):
    def eval(self, frame):
        one = frame.pop()
        frame.pop()
        frame.push(one)


class BaseBinaryBitwiseOp(Opcode):
    pass


class URSH(BaseBinaryBitwiseOp):
    def eval(self, frame):
        rval = frame.pop()
        lval = frame.pop()

        rnum = rval.get_int()
        lnum = lval.get_int()

        shift_count = rnum & 0x1F
        res = lnum >> shift_count

        frame.push(W_IntObject(res))


class RSH(BaseBinaryBitwiseOp):
    def eval(self, frame):
        rval = frame.pop()
        lval = frame.pop()

        rnum = rval.get_int()
        lnum = lval.get_int()

        shift_count = rnum & 0x1F
        res = lnum >> shift_count

        frame.push(W_IntObject(res))


class LSH(BaseBinaryBitwiseOp):
    def eval(self, frame):
        rval = frame.pop()
        lval = frame.pop()

        rnum = rval.get_int()
        lnum = lval.get_int()

        shift_count = rnum & 0x1F
        res = lnum << shift_count

        frame.push(W_IntObject(res))


class Opcodes:
    pass

# different opcode mappings, to make annotator happy

OpcodeMap = {}

for name, value in locals().items():
    if name.upper() == name and type(value) == type(Opcode) \
            and issubclass(value, Opcode):
        OpcodeMap[name] = value

opcodes = Opcodes()
for name, value in OpcodeMap.items():
    setattr(opcodes, name, value)
