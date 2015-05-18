"""This file contains both an interpreter and "hints" in the interpreter code
necessary to construct a Jit.

There are two required hints:
1. JitDriver.jit_merge_point() at the start of the opcode dispatch loop
2. JitDriver.can_enter_jit() at the end of loops (where they jump back)

These bounds and the "green" variables effectively mark loops and
allow the jit to decide if a loop is "hot" and in need of compiling.

Read http://doc.pypy.org/en/latest/jit/pyjitpl5.html for details.

"""

from pyhp.opcodes import BaseJump, RETURN
from pyhp.frame import GlobalFrame
from pyhp.objspace import ObjectSpace, newstring
from pyhp.stdlib import functions as global_functions
from pyhp.datatypes import W_Reference, W_Array

from rpython.rlib import jit
from rpython.rlib.rstring import UnicodeBuilder

import os


def printable_loc(pc, bc):
    opcode = bc._get_opcode(pc)
    # get_printable_location function must return a string
    # opcode string representation is a unicode string and thus needs encoding
    return "%d: %s" % (pc, opcode.str().encode("utf-8"))

driver = jit.JitDriver(reds=['frame', 'self'],
                       greens=['pc', 'bytecode'],
                       virtualizables=['frame'],
                       get_printable_location=printable_loc)


class Interpreter(object):
    _immutable_fields_ = ['space']

    def __init__(self):
        self.space = ObjectSpace(global_functions)
        self.output_buffer = []
        self.superglobals = []

    def run(self, bytecode):
        frame = GlobalFrame(self, bytecode)
        self.execute(bytecode, frame)

        # close any remaining buffers
        while len(self.output_buffer) > 0:
            buffer = self.end_buffer()
            self.output(buffer)

    def run_return(self, bytecode):
        self.start_buffering()

        frame = GlobalFrame(self, bytecode)
        self.execute(bytecode, frame)

        # close any remaining buffers
        while len(self.output_buffer) > 0:
            buffer = self.end_buffer()
            if len(self.output_buffer) > 0:
                self.output(buffer)
            else:
                return buffer

    def setup(self, request):
        get = W_Array()
        for name, value in request.get.iteritems():
            key = newstring(unicode(name))
            value = newstring(unicode(value))
            get.put(key, value)
        getref = W_Reference(get)

        # structure of this list needs to match pyhp.scopes.SUPERGLOBALS
        # SUPERGLOBALS = [u'$_GET', u'$_POST']
        self.superglobals = [getref, None]

    def execute(self, bytecode, frame):
        from pyhp.bytecode import ByteCode
        assert(isinstance(bytecode, ByteCode))
        from pyhp.frame import Frame
        assert(isinstance(frame, Frame))

        if bytecode._opcode_count() == 0:
            return None

        pc = 0
        while True:
            # required hint indicating this is the top of the opcode dispatch
            driver.jit_merge_point(pc=pc, bytecode=bytecode,
                                   self=self, frame=frame)

            if pc >= bytecode._opcode_count():
                return None

            opcode = bytecode._get_opcode(pc)

            if isinstance(opcode, RETURN):
                return frame.pop()

            opcode.eval(self, frame)

            if isinstance(opcode, BaseJump):
                new_pc = opcode.do_jump(frame, pc)
                if new_pc < pc:
                    driver.can_enter_jit(pc=new_pc, bytecode=bytecode,
                                         self=self, frame=frame)
                pc = new_pc
                continue
            else:
                pc += 1

    def declare_function(self, name, func):
        declared = self.space.declare_function(name, func)

        if not declared:
            raise Exception(u'Function %s alredy declared' % name)

    def get_function(self, name):
        return self.space.get_function(name)

    def declare_constant(self, name, value):
        return self.space.declare_constant(name, value)

    def get_constant(self, name):
        return self.space.get_constant(name)

    def start_buffering(self):
        self.output_buffer.append(UnicodeBuilder())

    def end_buffer(self):
        buffer = self.output_buffer[-1].build()
        self.output_buffer.pop()
        return buffer

    def output(self, string, buffer=True):
        if buffer and len(self.output_buffer) > 0:
            self.output_buffer[-1].append(string)
        else:
            self._output(string)

    def _output(self, string):
        assert isinstance(string, unicode)
        # 1 here represents stdout
        os.write(1, string.encode('utf-8'))
