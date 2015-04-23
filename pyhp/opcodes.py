from pyhp.datatypes import W_IntObject, W_StringObject, \
    W_Null, W_Array, W_Boolean, W_FloatObject, NativeFunction, W_Root
from pyhp.datatypes import compare_gt, compare_ge, compare_lt, compare_le, \
    compare_eq
from pyhp.datatypes import plus, increment, decrement, sub, mult, division

from pyhp.interpreter import execute
from pyhp.utils import printf


class Opcode(object):
    def __init__(self):
        pass

    def get_name(self):
        return self.__class__.__name__

    def eval(self, frame):
        """ Execute in frame
        """
        raise NotImplementedError(self.get_name() + ".eval")


class LOAD_CONSTANT(Opcode):
    pass


class LOAD_VAR(Opcode):
    def __init__(self, index, name):
        self.index = index
        self.name = name

    def eval(self, frame):
        variable = frame.get_var(self.index, self.name)
        if variable is None:
            raise Exception("Variable %s (%s) is not set" %
                            (self.index, self.name))
        frame.push(variable)


class LOAD_FUNCTION(Opcode):
    def __init__(self, function):
        self.function = function

    def eval(self, frame):
        frame.push(self.function)


class LOAD_LIST(Opcode):
    def __init__(self, number):
        self.number = number

    def eval(self, frame):
        arguments = [None] * self.number
        for i in range(self.number):
            index = self.number - 1 - i
            arguments[index] = frame.pop()
        frame.push(arguments)


class LOAD_NULL(Opcode):
    def eval(self, frame):
        frame.push(W_Null())


class LOAD_BOOLEAN(Opcode):
    def __init__(self, value):
        self.value = W_Boolean(value)

    def eval(self, frame):
        frame.push(self.value)


class LOAD_INTVAL(Opcode):
    def __init__(self, value):
        self.value = W_IntObject(value)

    def eval(self, frame):
        frame.push(self.value)


class LOAD_FLOATVAL(Opcode):
    def __init__(self, value):
        self.value = W_FloatObject(value)

    def eval(self, frame):
        frame.push(self.value)


class LOAD_STRINGVAL(Opcode):
    def __init__(self, value):
        self.value = W_StringObject(value)

    def eval(self, frame):
        stringval = self.value
        for variable in stringval.get_variables():
            search, identifier, indexes = variable
            index = frame.scope.get_index(identifier)
            assert index >= 0
            value = frame.get_var(index, identifier)
            for key in indexes:
                if key[0] == '$':
                    index = frame.scope.get_index(key)
                    assert index >= 0
                    key = frame.get_var(index, identifier).str()
                value = value.get(key)
            replace = value.str()
            stringval = stringval.replace(search, replace)

        frame.push(stringval)


class LOAD_ARRAY(Opcode):
    def __init__(self, number):
        self.number = number

    def eval(self, frame):
        array = W_Array()
        for i in range(self.number):
            index = str(self.number - 1 - i)
            array.put(index, frame.pop())
        frame.push(array)


class LOAD_MEMBER(Opcode):
    def eval(self, frame):
        array = frame.pop()
        member = frame.pop().str()
        value = array.get(member)
        frame.push(value)


class STORE_MEMBER(Opcode):
    def eval(self, frame):
        array = frame.pop()
        index = frame.pop().str()
        value = frame.pop()
        array.put(index, value)


class ASSIGN(Opcode):
    def __init__(self, index, name):
        self.index = index
        self.name = name

    def eval(self, frame):
        frame.set_var(self.index, self.name, frame.pop())


class DISCARD_TOP(Opcode):
    def eval(self, frame):
        frame.pop()


class DUP(Opcode):
    def eval(self, frame):
        frame.push(frame.top())


class BaseJump(Opcode):
    def __init__(self, where):
        self.where = where

    def eval(self, frame):
        pass


class JUMP_IF_FALSE(BaseJump):
    def do_jump(self, frame, pos):
        value = frame.pop()
        true = value
        if isinstance(value, W_Root):
            true = value.is_true()
        if not true:
            return self.where
        return pos + 1

    def __str__(self):
        return 'JUMP_IF_FALSE %d' % (self.where)


class JUMP(BaseJump):
    def do_jump(self, frame, pos):
        return self.where

    def __str__(self):
        return 'JUMP %d' % (self.where)


class RETURN(Opcode):
    def eval(self, frame):
        if frame.valuestack_pos > 0:
            return frame.pop()
        else:
            return W_Null()


class PRINT(Opcode):
    def eval(self, frame):
        item = frame.pop()
        printf(item.str())


class CALL(Opcode):
    def eval(self, frame):
        method = frame.pop()
        params = frame.pop()

        if isinstance(method, NativeFunction):
            res = method.call(*params)
        else:
            new_bc = method.body
            new_frame = frame.create_new_frame(new_bc.symbols)

            param_index = 0
            # reverse args index to preserve order
            for variable in new_bc.params():
                index = new_frame.scope.get_index(variable)
                assert index >= 0
                new_frame.vars[index] = params[param_index]
                param_index += 1

            res = execute(new_frame, new_bc)
        frame.push(res)


class EQ(Opcode):
    def eval(self, frame):
        right = frame.pop()
        left = frame.pop()
        frame.push(compare_eq(left, right))


class GT(Opcode):
    def eval(self, frame):
        right = frame.pop()
        left = frame.pop()
        frame.push(compare_gt(left, right))


class GE(Opcode):
    def eval(self, frame):
        right = frame.pop()
        left = frame.pop()
        frame.push(compare_ge(left, right))


class LT(Opcode):
    def eval(self, frame):
        right = frame.pop()
        left = frame.pop()
        frame.push(compare_lt(left, right))


class LE(Opcode):
    def eval(self, frame):
        right = frame.pop()
        left = frame.pop()
        frame.push(compare_le(left, right))


class AND(Opcode):
    def eval(self, frame):
        right = frame.pop()
        left = frame.pop()
        frame.push(left and right)


class OR(Opcode):
    def eval(self, frame):
        right = frame.pop()
        left = frame.pop()
        frame.push(left or right)


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


class INCR(Opcode):
    def eval(self, frame):
        left = frame.pop()
        frame.push(increment(left))


class DECR(Opcode):
    def eval(self, frame):
        left = frame.pop()
        frame.push(decrement(left))


class MOD(Opcode):
    pass


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
