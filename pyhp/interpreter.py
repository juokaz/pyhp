"""This file contains both an interpreter and "hints" in the interpreter code
necessary to construct a Jit.

There are two required hints:
1. JitDriver.jit_merge_point() at the start of the opcode dispatch loop
2. JitDriver.can_enter_jit() at the end of loops (where they jump back)

These bounds and the "green" variables effectively mark loops and
allow the jit to decide if a loop is "hot" and in need of compiling.

Read http://doc.pypy.org/en/latest/jit/pyjitpl5.html for details.

"""

from rpython.rlib import jit

from pyhp.datatypes import W_Null


def printable_loc(pc, code, bc):
    bytecode = bc.opcodes[pc]
    return str(pc) + " " + str(bytecode)

driver = jit.JitDriver(greens=['pc', 'opcodes', 'bc'],
                       reds=['frame'],
                       virtualizables=['frame'],
                       get_printable_location=printable_loc)


class Frame(object):
    _virtualizable_ = ['valuestack[*]', 'parent', 'valuestack_pos', 'vars']

    def __init__(self, scope, parent_frame=None):
        self = jit.hint(self, fresh_virtualizable=True, access_directly=True)
        self.valuestack = [None] * 50  # safe estimate!
        self.vars = {}
        self.valuestack_pos = 0

        self.scope = scope
        self.parent_frame = parent_frame

    def create_new_frame(self, scope):
        if isinstance(self.parent_frame, Frame):
            parent_frame = self.parent_frame
        else:
            parent_frame = self

        return Frame(scope, parent_frame)

    def is_visible(self, name):
        if self.parent_frame is None:
            return False

        # a global variable
        if name in self.scope.globals:
            return True

        if name in self.parent_frame.scope.functions:
            return True

        return self.parent_frame.is_visible(name)

        return False

    def get_var(self, index, name):
        assert index >= 0
        variable = self.vars.get(index)

        if variable is not None:
            return variable

        # if the current cuntext has access to a global variable read that
        if self.is_visible(name):
            return self.parent_frame.get_var(index, name)

        return None

    def set_var(self, index, name, value):
        assert index >= 0

        # if it is a parent (global) variable write to that instead
        if self.is_visible(name):
            self.parent_frame.set_var(index, name, value)
            return

        self.vars[index] = value

    def push(self, v):
        pos = jit.hint(self.valuestack_pos, promote=True)

        # prevent stack overflow
        len_stack = len(self.valuestack)
        assert pos >= 0 and len_stack > pos

        self.valuestack[pos] = v
        self.valuestack_pos = pos + 1

    def pop(self):
        pos = jit.hint(self.valuestack_pos, promote=True)
        new_pos = pos - 1
        assert new_pos >= 0
        v = self.valuestack[new_pos]
        self.valuestack_pos = new_pos
        return v

    def top(self):
        pos = self.valuestack_pos - 1
        assert pos >= 0
        return self.valuestack[pos]

    def __repr__(self):
        return "Frame %s, parent %s" % (self.vars, self.parent_frame)


def execute(frame, bc):
    opcodes = bc.opcodes
    pc = 0
    result = None
    while True:
        # required hint indicating this is the top of the opcode dispatch
        driver.jit_merge_point(pc=pc, opcodes=opcodes, bc=bc, frame=frame)

        if pc >= len(opcodes):
            break

        opcode = opcodes[pc]
        result = opcode.eval(frame)

        if result is not None:
            break

        if hasattr(opcode, 'do_jump'):
            new_pc = opcode.do_jump(frame, pc)
            if new_pc < pc:
                driver.jit_merge_point(pc=pc, opcodes=opcodes, bc=bc,
                                       frame=frame)
            pc = new_pc
            continue
        else:
            pc += 1

    if result is None:
        result = W_Null()

    return result
