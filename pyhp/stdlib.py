from pyhp.functions import NativeFunction
from pyhp.datatypes import W_CodeFunction
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

# ----- #


def new_native_function(name, function, params=[]):
    func = NativeFunction(name, function)
    obj = W_CodeFunction(func)
    return obj

functions = [
    new_native_function('strlen', strlen),
    new_native_function('str_repeat', str_repeat),
    new_native_function('dechex', dechex),
    new_native_function('number_format', number_format),
    new_native_function('range', array_range),
    new_native_function('gettimeofday', gettimeofday),
]
