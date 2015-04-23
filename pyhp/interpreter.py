"""This file contains both an interpreter and "hints" in the interpreter code
necessary to construct a Jit.

There are two required hints:
1. JitDriver.jit_merge_point() at the start of the opcode dispatch loop
2. JitDriver.can_enter_jit() at the end of loops (where they jump back)

These bounds and the "green" variables effectively mark loops and
allow the jit to decide if a loop is "hot" and in need of compiling.

Read http://doc.pypy.org/en/latest/jit/pyjitpl5.html for details.

"""

from pyhp import bytecode
from rpython.rlib import jit

from pyhp.utils import printf

from pyhp.datatypes import W_IntObject, W_StringObject, \
    W_Null, W_Array, W_Boolean, W_FloatObject
from pyhp.datatypes import plus, increment, decrement, sub, mult, division
from pyhp.datatypes import compare_gt, compare_ge, compare_lt, compare_le, \
    compare_eq


def printable_loc(pc, code, bc):
    bytecode = bc.opcodes[pc]
    return str(pc) + " " + str(bytecode)

driver = jit.JitDriver(greens=['pc', 'opcodes', 'bc'],
                       reds=['frame'],
                       virtualizables=['frame'],
                       get_printable_location=printable_loc)


class Frame(object):
    _virtualizable_ = ['valuestack[*]', 'parent', 'valuestack_pos', 'vars[*]']

    def __init__(self, scope, global_env=None):
        self = jit.hint(self, fresh_virtualizable=True, access_directly=True)
        self.valuestack = [None] * 100  # safe estimate!
        self.vars = [None] * 100
        self.valuestack_pos = 0

        self.arg_pos = 0
        self.argstack = [None] * 10  # safe estimate!

        self.scope = scope
        self.global_env = global_env

    def get_global_env(self):
        if self.global_env:
            return self.global_env
        return self

    def is_parent_visible(self, name):
        # a global variable
        if name in self.scope.globals:
            return True

        if self.global_env is not None and name in self.global_env.scope.functions:
            return True

        return False

    def get_var(self, index, name):
        variable = self.vars[index]

        if variable is not None:
            return variable

        # if the current cuntext has access to a global variable read that
        if self.global_env is not None and self.is_parent_visible(name):
            return self.global_env.get_var(index, name)

        return None

    def set_var(self, index, name, value):
        # if it is a parent (global) variable write to that instead
        if self.global_env is not None and self.is_parent_visible(name):
            self.global_env.set_var(index, name, value)
            return

        self.vars[index] = value

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

    def __repr__(self):
        return "Frame %s" % (self.vars)


def execute(frame, bc):
    opcodes = bc.opcodes
    pc = 0
    while True:
        # required hint indicating this is the top of the opcode dispatch
        driver.jit_merge_point(pc=pc, opcodes=opcodes, bc=bc, frame=frame)

        if pc >= len(opcodes):
            return W_Null()

        opcode = opcodes[pc]
        c = opcode.bytecode
        args = opcode.args

        pc += 1

        if c == bytecode.LOAD_STRINGVAL:
            stringval = W_StringObject(args[0])
            for variable in stringval.get_variables():
                search, identifier, indexes = variable
                index = bc.index_for_symbol(identifier)
                assert index >= 0
                value = frame.get_var(index, identifier)
                for key in indexes:
                    if key[0] == '$':
                        index = bc.index_for_symbol(key)
                        assert index >= 0
                        key = frame.get_var(index, identifier).str()
                    value = value.get(key)
                replace = value.str()
                stringval = stringval.replace(search, replace)

            frame.push(stringval)
        elif c == bytecode.LOAD_INTVAL:
            frame.push(W_IntObject(args[0]))
        elif c == bytecode.LOAD_FLOATVAL:
            frame.push(W_FloatObject(args[0]))
        elif c == bytecode.LOAD_VAR:
            variable = frame.get_var(args[0], args[1])
            if variable is None:
                raise Exception("Variable %s (%s) is not set" %
                                (args[0], args[1]))
            frame.push(variable)
        elif c == bytecode.LOAD_FUNCTION:
            frame.push(args[0])
        elif c == bytecode.LOAD_NULL:
            frame.push(W_Null())
        elif c == bytecode.LOAD_BOOLEAN:
            frame.push(W_Boolean(args[0]))
        elif c == bytecode.LOAD_PARAM:
            frame.push_arg(frame.pop())  # push to the argument-stack
        elif c == bytecode.LOAD_ARRAY:
            array = W_Array()
            for i in range(args[0]):
                index = str(args[0] - 1 - i)
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
        elif c == bytecode.ASSIGN:
            assert args[0] >= 0
            frame.set_var(args[0], args[1], frame.pop())
        elif c == bytecode.DISCARD_TOP:
            frame.pop()
        elif c == bytecode.RETURN:
            if frame.valuestack_pos > 0:
                return frame.pop()
            else:
                return W_Null()
        elif c == bytecode.LT:
            right = frame.pop()
            left = frame.pop()
            frame.push(compare_lt(left, right))
        elif c == bytecode.LE:
            right = frame.pop()
            left = frame.pop()
            frame.push(compare_le(left, right))
        elif c == bytecode.GT:
            right = frame.pop()
            left = frame.pop()
            frame.push(compare_gt(left, right))
        elif c == bytecode.GE:
            right = frame.pop()
            left = frame.pop()
            frame.push(compare_ge(left, right))
        elif c == bytecode.EQ:
            right = frame.pop()
            left = frame.pop()
            frame.push(compare_eq(left, right))
        elif c == bytecode.INCR:
            left = frame.pop()
            frame.push(increment(left))
        elif c == bytecode.DECR:
            left = frame.pop()
            frame.push(decrement(left))
        elif c == bytecode.ADD:
            right = frame.pop()
            left = frame.pop()
            frame.push(plus(left, right))
        elif c == bytecode.SUB:
            right = frame.pop()
            left = frame.pop()
            frame.push(sub(left, right))
        elif c == bytecode.MUL:
            right = frame.pop()
            left = frame.pop()
            frame.push(mult(left, right))
        elif c == bytecode.DIV:
            right = frame.pop()
            left = frame.pop()
            frame.push(division(left, right))
        elif c == bytecode.AND:
            right = frame.pop()
            left = frame.pop()
            frame.push(left and right)
        elif c == bytecode.OR:
            right = frame.pop()
            left = frame.pop()
            frame.push(left or right)
        elif c == bytecode.JUMP:
            pc = args[0]
        elif c == bytecode.JUMP_IF_FALSE:
            if not frame.pop():
                pc = args[0]
        elif c == bytecode.JUMP_BACKWARD:
            pc = args[0]
            # required hint indicating this is the end of a loop
            driver.can_enter_jit(pc=pc, opcodes=opcodes, bc=bc, frame=frame)
        elif c == bytecode.CALL:
            method = frame.pop()

            if not hasattr(method, 'body'):
                raise Exception("Unsupported function variable %s" % method)

            new_bc = method.body
            new_frame = Frame(new_bc.symbols, frame.get_global_env())

            params_length = len(new_bc.params())
            params = [None] * params_length

            # reverse args index to preserve order
            for i in range(params_length):
                index = params_length - 1 - i
                assert index >= 0
                params[index] = frame.pop_arg()

            param_index = 0
            # reverse args index to preserve order
            for variable in new_bc.params():
                index = new_bc.index_for_symbol(variable)
                assert index >= 0
                new_frame.vars[index] = params[param_index]
                param_index += 1

            res = execute(new_frame, new_bc)
            frame.push(res)
        elif c == bytecode.PRINT:
            item = frame.pop()
            printf(item.str())
        else:
            raise Exception("Unkown operation %s" % bytecode.bytecodes[c])
