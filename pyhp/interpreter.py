"""This file contains both an interpreter and "hints" in the interpreter code
necessary to construct a Jit.

There are two required hints:
1. JitDriver.jit_merge_point() at the start of the opcode dispatch loop
2. JitDriver.can_enter_jit() at the end of loops (where they jump back)

These bounds and the "green" variables effectively mark loops and
allow the jit to decide if a loop is "hot" and in need of compiling.

Read http://doc.pypy.org/en/latest/jit/pyjitpl5.html for details.

"""

from pyhp.sourceparser import parse
from pyhp.bytecode import compile_ast
from pyhp import bytecode
from rpython.rlib import jit

from utils import printf


def printable_loc(pc, code, bc):
    return str(pc) + " " + bytecode.bytecodes[ord(code[pc])]

driver = jit.JitDriver(greens=['pc', 'code', 'bc'],
                       reds=['frame'],
                       virtualizables=['frame'],
                       get_printable_location=printable_loc)


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
        self.stringval = stringval

    def append(self, other):
        if not isinstance(other, W_StringObject):
            raise Exception("wrong type")
        return W_StringObject(self.stringval + other.stringval)

    def str(self):
        return str(self.stringval)


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


class Frame(object):
    _virtualizable_ = ['valuestack[*]', 'valuestack_pos', 'vars[*]']

    def __init__(self, bc):
        self = jit.hint(self, fresh_virtualizable=True, access_directly=True)
        self.valuestack = [None] * 3  # safe estimate!
        self.vars = [None] * bc.numvars
        self.valuestack_pos = 0

        self.arg_pos = 0
        self.argstack = [None] * 3  # safe estimate!

    def push(self, v):
        pos = jit.hint(self.valuestack_pos, promote=True)
        assert pos >= 0
        self.valuestack[pos] = v
        self.valuestack_pos = pos + 1

    def pop(self):
        pos = jit.hint(self.valuestack_pos, promote=True)
        new_pos = pos - 1
        assert new_pos >= 0
        v = self.valuestack[new_pos]
        self.valuestack_pos = new_pos
        return v

    def push_arg(self, v):
        argpos = jit.hint(self.arg_pos, promote=True)
        assert argpos >= 0, 'Argstack underflow'
        self.argstack[argpos] = v

        self.arg_pos = argpos + 1

    def pop_arg(self):
        argpos = jit.hint(self.arg_pos, promote=True)
        new_pos = argpos - 1
        assert new_pos >= 0, 'Argstack underflow'
        result = self.argstack[new_pos]
        self.arg_pos = new_pos

        return result


def execute(frame, bc):
    code = bc.code
    pc = 0
    while True:
        # required hint indicating this is the top of the opcode dispatch
        driver.jit_merge_point(pc=pc, code=code, bc=bc, frame=frame)

        if pc >= len(code):
            return W_Null()

        c = ord(code[pc])
        arg = ord(code[pc + 1])
        pc += 2
        if c == bytecode.LOAD_CONSTANT:
            w_constant = bc.constants[arg]
            frame.push(w_constant)
        elif c == bytecode.LOAD_VAR:
            frame.push(frame.vars[arg])
        elif c == bytecode.LOAD_NULL:
            frame.push(W_Null())
        elif c == bytecode.LOAD_BOOLEAN:
            frame.push(W_Boolean(bool(arg)))
        elif c == bytecode.LOAD_PARAM:
            frame.push_arg(frame.pop())  # push to the argument-stack
        elif c == bytecode.LOAD_ARRAY:
            array = W_Array()
            for i in range(arg):
                index = str(arg - 1 - i)
                array.put(index, frame.pop())
            frame.push(array)
        elif c == bytecode.LOAD_MEMBER:
            array = frame.pop()
            member = frame.pop().str()
            value = array.get(member)
            frame.push(value)
        elif c == bytecode.STORE_MEMBER:
            array = frame.pop()
            index = frame.pop().str()
            value = frame.pop()
            array.put(index, value)
        elif c == bytecode.DISCARD_TOP:
            frame.pop()
        elif c == bytecode.RETURN:
            if frame.valuestack_pos > 0:
                return frame.pop()
            else:
                return W_Null()
        elif c == bytecode.BINARY_ADD:
            right = frame.pop()
            left = frame.pop()
            w_res = left.add(right)
            frame.push(w_res)
        elif c == bytecode.BINARY_LT:
            right = frame.pop()
            left = frame.pop()
            frame.push(left.lt(right))
        elif c == bytecode.BINARY_GE:
            right = frame.pop()
            left = frame.pop()
            frame.push(left.ge(right))
        elif c == bytecode.BINARY_EQ:
            right = frame.pop()
            left = frame.pop()
            frame.push(left.eq(right))
        elif c == bytecode.BINARY_SUB:
            right = frame.pop()
            left = frame.pop()
            frame.push(left.sub(right))
        elif c == bytecode.BINARY_STRINGJOIN:
            right = frame.pop()
            left = frame.pop()
            frame.push(left.append(right))
        elif c == bytecode.JUMP_IF_FALSE:
            if not frame.pop().is_true():
                pc = arg
        elif c == bytecode.JUMP_BACKWARD:
            pc = arg
            # required hint indicating this is the end of a loop
            driver.can_enter_jit(pc=pc, code=code, bc=bc, frame=frame)
        elif c == bytecode.CALL:
            method = bc.functions[arg]
            method.body.globals = [None]*bc.numvars  # XXX

            new_bc = method.body
            new_frame = Frame(new_bc)

            # reverse args index to preserve order
            for i in range(len(method.params)):
                index = len(method.params) - 1 - i
                assert index >= 0
                new_frame.vars[index] = frame.pop_arg()

            res = execute(new_frame, new_bc)
            frame.push(res)
        elif c == bytecode.PRINT:
            item = frame.pop()
            printf(item.str())
        elif c == bytecode.ASSIGN:
            assert arg >= 0
            frame.vars[arg] = frame.pop()
        else:
            raise Exception("Unkown operation %s" % bytecode.bytecodes[c])


def interpret(source):
    bc = compile_ast(parse(source))
    frame = Frame(bc)
    execute(frame, bc)
    return frame  # for tests and later introspection
