from pyhp.datatypes import W_Function, W_CodeFunction, W_Iterator
from pyhp.datatypes import compare_gt, compare_ge, compare_lt, compare_le, \
    compare_eq

from rpython.rlib import jit


class Opcode(object):
    _settled_ = True
    _immutable_fields_ = ['_stack_change']
    _stack_change = 1

    def __init__(self):
        pass

    def get_name(self):
        return self.__class__.__name__

    def eval(self, interpreter, bytecode, frame, space):
        """ Execute in frame
        """
        raise NotImplementedError(self.get_name() + ".eval")

    def stack_change(self):
        return self._stack_change

    def str(self):
        return unicode(self.get_name())

    def __str__(self):
        return self.str()


class LOAD_NAMED_CONSTANT(Opcode):
    _immutable_fields_ = ['_stack_change', 'name']
    _stack_change = 1

    def __init__(self, name):
        self.name = name

    def eval(self, interpreter, bytecode, frame, space):
        value = space.get_constant(self.name)
        if value is None:
            raise Exception(u"Constant %s is not defined" % self.name)
        frame.push(value)

    def str(self):
        return u'LOAD_NAMED_CONSTANT %s' % (self.name)


class LOAD_VAR(Opcode):
    _immutable_fields_ = ['_stack_change', 'index', 'name']
    _stack_change = 1

    def __init__(self, index, name):
        self.index = index
        self.name = name

    def eval(self, interpreter, bytecode, frame, space):
        variable = frame.get_variable(self.name, self.index)

        if variable is None:
            raise Exception(u"Variable %s is not set" % self.name)

        frame.push(variable)

    def str(self):
        return u'LOAD_VAR %d, %s' % (self.index, self.name)


class LOAD_REF(Opcode):
    _immutable_fields_ = ['_stack_change', 'index', 'name']
    _stack_change = 1

    def __init__(self, index, name):
        self.index = index
        self.name = name

    def eval(self, interpreter, bytecode, frame, space):
        ref = frame.get_reference(self.name, self.index)

        if ref is None:
            raise Exception(u"Variable %s is not set" % self.name)

        frame.push(ref)

    def str(self):
        return u'LOAD_REF %d, %s' % (self.index, self.name)


class LOAD_FUNCTION(Opcode):
    _immutable_fields_ = ['_stack_change', 'name']
    _stack_change = 1

    def __init__(self, name):
        self.name = name

    def eval(self, interpreter, bytecode, frame, space):
        func = space.get_function(self.name)
        if func is None:
            raise Exception(u"Function %s is not defined" % self.name)
        frame.push(func)

    def str(self):
        return u'LOAD_FUNCTION %s' % (self.name)


class DECLARE_FUNCTION(Opcode):
    _immutable_fields_ = ['_stack_change', 'name', 'bytecode']
    _stack_change = 0

    def __init__(self, name, bytecode):
        self.name = name
        self.bytecode = bytecode

    def eval(self, interpreter, bytecode, frame, space):
        funcobj = W_CodeFunction(self.bytecode)

        if space.get_function(self.name):
            raise Exception(u'Function %s alredy declared' % self.name)

        space.declare_function(self.name, funcobj)

    def str(self):
        return u'DECLARE_FUNCTION %s' % (self.name)


class LOAD_NULL(Opcode):
    _stack_change = 1

    def eval(self, interpreter, bytecode, frame, space):
        frame.push(space.w_Null)

    def str(self):
        return u'LOAD_NULL'


class LOAD_BOOLEAN(Opcode):
    _immutable_fields_ = ['_stack_change', 'value']
    _stack_change = 1

    def __init__(self, value):
        self.value = value

    def eval(self, interpreter, bytecode, frame, space):
        if self.value:
            frame.push(space.w_True)
        else:
            frame.push(space.w_False)

    def str(self):
        if self.value:
            return u'LOAD_BOOLEAN True'
        else:
            return u'LOAD_BOOLEAN False'


class STRING_SUBSTITUTION(Opcode):
    _immutable_fields_ = ['_stack_change', 'number']

    def __init__(self, number):
        self.number = number
        self._stack_change = -1 + (-1 * self.number) + 1

    @jit.unroll_safe
    def eval(self, interpreter, bytecode, frame, space):
        string = frame.pop()

        parts = frame.pop_n(self.number)

        frame.push(string.substitute(parts))

    def str(self):
        return u'STRING_SUBSTITUTION %d' % (self.number)


class LOAD_ARRAY(Opcode):
    _immutable_fields_ = ['_stack_change', 'number']

    def __init__(self, number):
        self.number = number
        self._stack_change = (-1 * self.number) + 1

    @jit.unroll_safe
    def eval(self, interpreter, bytecode, frame, space):
        list_w = frame.pop_n(self.number)
        frame.push(space.wrap(list_w))

    def str(self):
        return u'LOAD_ARRAY %d' % (self.number)


class LOAD_CONSTANT(Opcode):
    _immutable_fields_ = ['_stack_change', 'index']
    _stack_change = 1

    def __init__(self, index):
        self.index = index

    def eval(self, interpreter, bytecode, frame, space):
        frame.push(bytecode._constants[self.index])

    def str(self):
        return u'LOAD_CONSTANT %d' % (self.index)


class LOAD_MEMBER(Opcode):
    _stack_change = -1

    def eval(self, interpreter, bytecode, frame, space):
        array = frame.pop()

        member = frame.pop()
        value = array.get(member)
        frame.push(value)


class LOAD_MEMBER_VAR(Opcode):
    _immutable_fields_ = ['_stack_change', 'index', 'name']
    _stack_change = 0

    def __init__(self, index, name):
        self.index = index
        self.name = name

    def eval(self, interpreter, bytecode, frame, space):
        array = frame.get_variable(self.name, self.index)

        if array is None:
            raise Exception(u"Variable %s is not set" % self.name)

        member = frame.pop()
        value = array.get(member)
        frame.push(value)

    def str(self):
        return u'LOAD_MEMBER_VAR %d, %s' % (self.index, self.name)


class STORE_MEMBER(Opcode):
    _stack_change = -2

    def eval(self, interpreter, bytecode, frame, space):
        array = frame.pop()
        index = frame.pop()
        value = frame.pop()
        array = array.put(index, value)
        # TODO here the array might have changed into a different instance
        # it needs to be stored in the frame
        frame.push(array)

    def str(self):
        return u'STORE_MEMBER'


class STORE_MEMBER_VAR(Opcode):
    _immutable_fields_ = ['_stack_change', 'index', 'name']
    _stack_change = -1

    def __init__(self, index, name):
        self.index = index
        self.name = name

    def eval(self, interpreter, bytecode, frame, space):
        array = frame.get_variable(self.name, self.index)

        if array is None:
            raise Exception(u"Variable %s is not set" % self.name)

        index = frame.pop()
        value = frame.pop()
        array = array.put(index, value)
        frame.push(array)

        frame.store_variable(self.name, self.index, array)

    def str(self):
        return u'STORE_MEMBER_VAR %d, %s' % (self.index, self.name)


class ASSIGN(Opcode):
    _immutable_fields_ = ['_stack_change', 'index', 'name']
    _stack_change = 0

    def __init__(self, index, name):
        self.index = index
        self.name = name

    def eval(self, interpreter, bytecode, frame, space):
        value = frame.pop()
        frame.store_variable(self.name, self.index, value)

        frame.push(value)

    def str(self):
        return u'ASSIGN %d, %s' % (self.index, self.name)


class DISCARD_TOP(Opcode):
    _stack_change = -1

    def eval(self, interpreter, bytecode, frame, space):
        frame.pop()


class DUP(Opcode):
    _stack_change = 1

    def eval(self, interpreter, bytecode, frame, space):
        frame.push(frame.top())


class LABEL(Opcode):
    _immutable_fields_ = ['_stack_change', 'num']
    _stack_change = 0

    def __init__(self, num):
        self.num = num

    def str(self):
        return u'LABEL %d' % (self.num)


class BaseJump(Opcode):
    _immutable_fields_ = ['_stack_change', 'where']
    _stack_change = -1

    def __init__(self, where):
        self.where = where

    def eval(self, interpreter, bytecode, frame, space):
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
    _stack_change = 0

    def do_jump(self, frame, pos):
        return self.where

    def str(self):
        return u'JUMP %d' % (self.where)


class LOAD_ITERATOR(Opcode):
    _stack_change = 0

    def eval(self, interpreter, bytecode, frame, space):
        obj = frame.pop()
        iterator = obj.to_iterator()

        frame.push(iterator)


class JUMP_IF_ITERATOR_EMPTY(BaseJump):
    _stack_change = 0

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
    _stack_change = 2

    def eval(self, interpreter, bytecode, frame, space):
        iterator = frame.top()
        assert isinstance(iterator, W_Iterator)
        key = iterator.key()
        value = iterator.current()
        frame.push(value)
        frame.push(key)
        iterator.next()


class RETURN(Opcode):
    _stack_change = -1

    def eval(self, interpreter, bytecode, frame, space):
        return frame.pop()


class PRINT(Opcode):
    _stack_change = 0

    def eval(self, interpreter, bytecode, frame, space):
        item = frame.top()
        interpreter.output(item.str())


class CALL(Opcode):
    _immutable_fields_ = ['_stack_change', 'arguments']

    def __init__(self, arguments):
        self.arguments = arguments
        self._stack_change = -1 + (-1 * self.arguments) + 1

    def eval(self, interpreter, bytecode, frame, space):
        method = frame.pop()

        assert isinstance(method, W_Function)

        params = frame.pop_n(self.arguments)

        res = method.call(interpreter, space, frame, params)
        frame.push(res)


class BaseDecision(Opcode):
    _stack_change = -1

    def eval(self, interpreter, bytecode, frame, space):
        right = frame.pop()
        left = frame.pop()
        res = self.decision(left, right)
        frame.push(space.wrap(res))

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


class BaseMathOperation(Opcode):
    _stack_change = -1


class CONCAT(BaseMathOperation):
    def eval(self, interpreter, bytecode, frame, space):
        right = frame.pop()
        left = frame.pop()
        frame.push(left.concat(right))


class ADD(BaseMathOperation):
    def eval(self, interpreter, bytecode, frame, space):
        right = frame.pop()
        left = frame.pop()
        frame.push(space.add(left, right))


class SUB(BaseMathOperation):
    def eval(self, interpreter, bytecode, frame, space):
        right = frame.pop()
        left = frame.pop()
        frame.push(space.sub(left, right))


class MUL(BaseMathOperation):
    def eval(self, interpreter, bytecode, frame, space):
        right = frame.pop()
        left = frame.pop()
        frame.push(space.mult(left, right))


class DIV(BaseMathOperation):
    def eval(self, interpreter, bytecode, frame, space):
        right = frame.pop()
        left = frame.pop()
        frame.push(space.div(left, right))


class MOD(BaseMathOperation):
    def eval(self, interpreter, bytecode, frame, space):
        right = frame.pop()
        left = frame.pop()
        frame.push(space.mod(left, right))


class BaseUnaryOperation(Opcode):
    _stack_change = 0


class NOT(BaseUnaryOperation):
    def eval(self, interpreter, bytecode, frame, space):
        val = frame.pop()
        boolval = val.is_true()
        frame.push(space.wrap(not boolval))


class INCR(BaseUnaryOperation):
    def eval(self, interpreter, bytecode, frame, space):
        left = frame.pop()
        frame.push(space.increment(left))


class DECR(BaseUnaryOperation):
    def eval(self, interpreter, bytecode, frame, space):
        left = frame.pop()
        frame.push(space.decrement(left))


class COMMA(BaseUnaryOperation):
    def eval(self, interpreter, bytecode, frame, space):
        one = frame.pop()
        frame.pop()
        frame.push(one)


class BaseBinaryBitwiseOp(Opcode):
    _stack_change = -1


class URSH(BaseBinaryBitwiseOp):
    def eval(self, interpreter, bytecode, frame, space):
        rval = frame.pop()
        lval = frame.pop()

        rnum = rval.get_int()
        lnum = lval.get_int()

        shift_count = rnum & 0x1F
        res = lnum >> shift_count

        frame.push(space.wrap(res))


class RSH(BaseBinaryBitwiseOp):
    def eval(self, interpreter, bytecode, frame, space):
        rval = frame.pop()
        lval = frame.pop()

        rnum = rval.get_int()
        lnum = lval.get_int()

        shift_count = rnum & 0x1F
        res = lnum >> shift_count

        frame.push(space.wrap(res))


class LSH(BaseBinaryBitwiseOp):
    def eval(self, interpreter, bytecode, frame, space):
        rval = frame.pop()
        lval = frame.pop()

        rnum = rval.get_int()
        lnum = lval.get_int()

        shift_count = rnum & 0x1F
        res = lnum << shift_count

        frame.push(space.wrap(res))


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
