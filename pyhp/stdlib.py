from pyhp.scopes import StdlibScope
from pyhp.datatypes import NativeFunction
from pyhp.datatypes import isint, isstr
from pyhp.datatypes import W_IntObject, W_StringObject, W_Array

import time
import math


def strlen(args):
    string = args[0]
    assert(isstr(string))
    return W_IntObject(string.len())


def str_repeat(args):
    string = args[0]
    repeat = args[1]
    assert(isstr(string))
    assert(isint(repeat))
    repeated = string.str() * repeat.get_int()
    return W_StringObject(repeated)


def dechex(args):
    number = args[0]
    assert(isint(number))
    return W_StringObject(hex(number.get_int()))


def number_format(args):
    number = args[0]
    positions = args[1]
    assert(isint(positions))

    number = number.to_number()
    shift = int(math.pow(10, positions.get_int()))
    usec = int(number * shift + 0.5) - int(number) * shift
    sec = int(number)

    formatted = "%s.%s" % (sec, usec)
    return W_StringObject(formatted)


def array_range(args):
    start = args[0]
    finish = args[1]
    assert(isint(start))
    assert(isint(finish))
    array = W_Array()
    for number in range(start.get_int(), finish.get_int()+1):
        array.put(str(number), W_IntObject(number))
    return array


def gettimeofday(args):
    seconds = time.time()
    usec = int(seconds * 1000000) - int(seconds) * 1000000
    sec = int(seconds)

    array = W_Array()
    array.put('sec', W_IntObject(sec))
    array.put('usec', W_IntObject(usec))
    return array

functions = [
    NativeFunction('strlen', strlen),
    NativeFunction('str_repeat', str_repeat),
    NativeFunction('dechex', dechex),
    NativeFunction('number_format', number_format),
    NativeFunction('range', array_range),
    NativeFunction('gettimeofday', gettimeofday),
]

scope = StdlibScope(functions[:])
