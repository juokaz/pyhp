from pyhp.datatypes import W_StringObject, \
    W_Array, W_List, \
    W_Function, W_CodeFunction, W_Iterator
from pyhp.objspace import w_Null, newbool, newint, newfloat, newstring
from pyhp.datatypes import compare_gt, compare_ge, compare_lt, compare_le, \
    compare_eq
from pyhp.datatypes import plus, increment, decrement, sub, mult, division, mod

from rpython.rlib import jit


class Opcode(object):
    _settled_ = True

    def __init__(self):
        pass

    def get_name(self):
        return self.__class__.__name__

    def eval(self, interpreter, frame):
        """ Execute in frame
        """
        raise NotImplementedError(self.get_name() + ".eval")

    def str(self):
        return unicode(self.get_name())

    def __str__(self):
        return self.str()


class LOAD_CONSTANT(Opcode):
    _immutable_fields_ = ['name']

    def __init__(self, name):
        self.name = name

    def eval(self, interpreter, frame):
        value = interpreter.get_constant(self.name)
        if value is None:
            raise Exception(u"Constant %s is not defined" % self.name)
        frame.push(value)

    def str(self):
        return u'LOAD_CONSTANT %s' % (self.name)


class LOAD_VAR(Opcode):
    _immutable_fields_ = ['index', 'name']

    def __init__(self, index, name):
        self.index = index
        self.name = name

    def eval(self, interpreter, frame):
        variable = frame.get_variable(self.name, self.index)

        if variable is None:
            raise Exception(u"Variable %s is not set" % self.name)

        frame.push(variable)

    def str(self):
        return u'LOAD_VAR %d, %s' % (self.index, self.name)


class LOAD_REF(Opcode):
    _immutable_fields_ = ['index', 'name']

    def __init__(self, index, name):
        self.index = index
        self.name = name

    def eval(self, interpreter, frame):
        ref = frame.get_reference(self.name, self.index)

        if ref is None:
            raise Exception(u"Variable %s is not set" % self.name)

        frame.push(ref)

    def str(self):
        return u'LOAD_REF %d, %s' % (self.index, self.name)


class LOAD_FUNCTION(Opcode):
    _immutable_fields_ = ['name']

    def __init__(self, name):
        self.name = name

    def eval(self, interpreter, frame):
        func = interpreter.get_function(self.name)
        if func is None:
            raise Exception(u"Function %s is not defined" % self.name)
        frame.push(func)

    def str(self):
        return u'LOAD_FUNCTION %s' % (self.name)


class DECLARE_FUNCTION(Opcode):
    _immutable_fields_ = ['name', 'bytecode']

    def __init__(self, name, bytecode):
        self.name = name
        self.bytecode = bytecode

    def eval(self, interpreter, frame):
        funcobj = W_CodeFunction(self.bytecode)
        interpreter.declare_function(self.name, funcobj)

    def str(self):
        return u'DECLARE_FUNCTION %s' % (self.name)


class LOAD_LIST(Opcode):
    _immutable_fields_ = ['number']

    def __init__(self, number):
        self.number = number

    def eval(self, interpreter, frame):
        list_w = frame.pop_n(self.number)
        frame.push(W_List(list_w))

    def str(self):
        return u'LOAD_LIST %d' % self.number


class LOAD_NULL(Opcode):
    def eval(self, interpreter, frame):
        frame.push(w_Null)

    def str(self):
        return u'LOAD_NULL'


class LOAD_BOOLEAN(Opcode):
    _immutable_fields_ = ['value']

    def __init__(self, value):
        self.value = newbool(value)

    def eval(self, interpreter, frame):
        frame.push(self.value)

    def str(self):
        return u'LOAD_BOOLEAN %s' % (self.value.str())


class LOAD_INTVAL(Opcode):
    _immutable_fields_ = ['value']

    def __init__(self, value):
        self.value = newint(value)

    def eval(self, interpreter, frame):
        frame.push(self.value)

    def str(self):
        return u'LOAD_INTVAL %s' % (self.value.str())


class LOAD_FLOATVAL(Opcode):
    _immutable_fields_ = ['value']

    def __init__(self, value):
        self.value = newfloat(value)

    def eval(self, interpreter, frame):
        frame.push(self.value)

    def str(self):
        return u'LOAD_FLOATVAL %s' % (self.value.str())


class LOAD_STRINGVAL(Opcode):
    _immutable_fields_ = ['value']

    def __init__(self, value):
        self.value = newstring(value)

    def eval(self, interpreter, frame):
        frame.push(self.value)

    def str(self):
        return u'LOAD_STRINGVAL "%s"' % (self.value.str())


class LOAD_STRING_SUBSTITUTION(Opcode):
    _immutable_fields_ = ['number']

    def __init__(self, number):
        self.number = number

    @jit.unroll_safe
    def eval(self, interpreter, frame):
        value = newstring(u'')
        list_w = frame.pop_n(self.number)

        for part in list_w:
            value = value.append(part.str())

        frame.push(value)

    def str(self):
        return u'LOAD_STRING_SUBSTITUTION %d' % (self.number)


class LOAD_ARRAY(Opcode):
    _immutable_fields_ = ['number']

    def __init__(self, number):
        self.number = number

    @jit.unroll_safe
    def eval(self, interpreter, frame):
        array = W_Array()
        list_w = frame.pop_n(self.number)
        for index, el in enumerate(list_w):
            array.put(newint(index), el)
        frame.push(array)

    def str(self):
        return u'LOAD_ARRAY %d' % (self.number)


class LOAD_MEMBER(Opcode):
    def eval(self, interpreter, frame):
        array = frame.pop()
        assert isinstance(array, W_Array) or isinstance(array, W_StringObject)

        member = frame.pop()
        value = array.get(member)
        frame.push(value)


class LOAD_MEMBER_VAR(Opcode):
    _immutable_fields_ = ['index', 'name']

    def __init__(self, index, name):
        self.index = index
        self.name = name

    def eval(self, interpreter, frame):
        array = frame.get_variable(self.name, self.index)

        if array is None:
            raise Exception(u"Variable %s is not set" % self.name)

        assert isinstance(array, W_Array) or isinstance(array, W_StringObject)

        member = frame.pop()
        value = array.get(member)
        frame.push(value)

    def str(self):
        return u'LOAD_MEMBER_VAR %d, %s' % (self.index, self.name)


class STORE_MEMBER(Opcode):
    def eval(self, interpreter, frame):
        array = frame.pop()
        index = frame.pop()
        value = frame.pop()
        array.put(index, value)

        frame.push(array)

    def str(self):
        return u'STORE_MEMBER'


class ASSIGN(Opcode):
    _immutable_fields_ = ['index', 'name']

    def __init__(self, index, name):
        self.index = index
        self.name = name

    def eval(self, interpreter, frame):
        value = frame.pop()
        frame.store_variable(self.name, self.index, value)

        frame.push(value)

    def str(self):
        return u'ASSIGN %d, %s' % (self.index, self.name)


class DISCARD_TOP(Opcode):
    def eval(self, interpreter, frame):
        frame.pop()


class DUP(Opcode):
    def eval(self, interpreter, frame):
        frame.push(frame.top())


class LABEL(Opcode):
    _immutable_fields_ = ['num']

    def __init__(self, num):
        self.num = num

    def str(self):
        return u'LABEL %d' % (self.num)


class BaseJump(Opcode):
    _immutable_fields_ = ['where']

    def __init__(self, where):
        self.where = where

    def eval(self, interpreter, frame):
        pass


class JUMP_IF_FALSE(BaseJump):
    def do_jump(self, frame, pos):
        value = frame.pop()
        if not value.is_true():
            return self.where
        return pos + 1

    def str(self):
        return u'JUMP_IF_FALSE %d' % (self.where)


class JUMP_IF_FALSE_NOPOP(BaseJump):
    def do_jump(self, frame, pos):
        value = frame.top()
        if not value.is_true():
            return self.where
        frame.pop()
        return pos + 1

    def str(self):
        return u'JUMP_IF_FALSE_NOPOP %d' % (self.where)


class JUMP_IF_TRUE_NOPOP(BaseJump):
    def do_jump(self, frame, pos):
        value = frame.top()
        if value.is_true():
            return self.where
        frame.pop()
        return pos + 1

    def str(self):
        return u'JUMP_IF_TRUE_NOPOP %d' % (self.where)


class JUMP(BaseJump):
    def do_jump(self, frame, pos):
        return self.where

    def str(self):
        return u'JUMP %d' % (self.where)


class LOAD_ITERATOR(Opcode):
    def eval(self, interpreter, frame):
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

    def str(self):
        return u'JUMP_IF_ITERATOR_EMPTY %d' % (self.where)


class NEXT_ITERATOR(Opcode):
    def eval(self, interpreter, frame):
        iterator = frame.top()
        assert isinstance(iterator, W_Iterator)
        key, value = iterator.next()
        frame.push(value)
        frame.push(key)


class RETURN(Opcode):
    def eval(self, interpreter, frame):
        return frame.pop()


class PRINT(Opcode):
    def eval(self, interpreter, frame):
        item = frame.top()
        interpreter.output(item.str())


class CALL(Opcode):
    def eval(self, interpreter, frame):
        method = frame.pop()
        params = frame.pop()

        assert isinstance(method, W_Function)
        assert isinstance(params, W_List)

        res = method.call(interpreter, frame, params.to_list())
        frame.push(res)


class BaseDecision(Opcode):
    def eval(self, interpreter, frame):
        right = frame.pop()
        left = frame.pop()
        res = self.decision(left, right)
        frame.push(newbool(res))

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
    def eval(self, interpreter, frame):
        right = frame.pop()
        left = frame.pop()
        frame.push(plus(left, right))


class SUB(Opcode):
    def eval(self, interpreter, frame):
        right = frame.pop()
        left = frame.pop()
        frame.push(sub(left, right))


class MUL(Opcode):
    def eval(self, interpreter, frame):
        right = frame.pop()
        left = frame.pop()
        frame.push(mult(left, right))


class DIV(Opcode):
    def eval(self, interpreter, frame):
        right = frame.pop()
        left = frame.pop()
        frame.push(division(left, right))


class MOD(Opcode):
    def eval(self, interpreter, frame):
        right = frame.pop()
        left = frame.pop()
        frame.push(mod(left, right))


class BaseUnaryOperation(Opcode):
    pass


class NOT(BaseUnaryOperation):
    def eval(self, interpreter, frame):
        val = frame.pop()
        boolval = val.is_true()
        frame.push(newbool(not boolval))


class INCR(BaseUnaryOperation):
    def eval(self, interpreter, frame):
        left = frame.pop()
        frame.push(increment(left))


class DECR(BaseUnaryOperation):
    def eval(self, interpreter, frame):
        left = frame.pop()
        frame.push(decrement(left))


class COMMA(BaseUnaryOperation):
    def eval(self, interpreter, frame):
        one = frame.pop()
        frame.pop()
        frame.push(one)


class BaseBinaryBitwiseOp(Opcode):
    pass


class URSH(BaseBinaryBitwiseOp):
    def eval(self, interpreter, frame):
        rval = frame.pop()
        lval = frame.pop()

        rnum = rval.get_int()
        lnum = lval.get_int()

        shift_count = rnum & 0x1F
        res = lnum >> shift_count

        frame.push(newint(res))


class RSH(BaseBinaryBitwiseOp):
    def eval(self, interpreter, frame):
        rval = frame.pop()
        lval = frame.pop()

        rnum = rval.get_int()
        lnum = lval.get_int()

        shift_count = rnum & 0x1F
        res = lnum >> shift_count

        frame.push(newint(res))


class LSH(BaseBinaryBitwiseOp):
    def eval(self, interpreter, frame):
        rval = frame.pop()
        lval = frame.pop()

        rnum = rval.get_int()
        lnum = lval.get_int()

        shift_count = rnum & 0x1F
        res = lnum << shift_count

        frame.push(newint(res))


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
