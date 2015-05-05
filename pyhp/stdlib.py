from pyhp.functions import NativeFunction
from pyhp.datatypes import W_CodeFunction
from pyhp.datatypes import isint, isstr
from pyhp.datatypes import W_IntObject, W_StringObject, W_Array, W_Null
from pyhp.utils import printf as printf_, StringFormatter

import time
from rpython.rlib.rfloat import formatd


def define(space, args):
    name = args[0]
    assert(isstr(name))
    value = args[1]
    space.declare_constant(name.str(), value)


def strlen(space, args):
    string = args[0]
    assert(isstr(string))
    return W_IntObject(string.len())


def str_repeat(space, args):
    string = args[0]
    repeat = args[1]
    assert(isstr(string))
    assert(isint(repeat))
    repeated = string.str() * repeat.get_int()
    return W_StringObject(repeated)


def printf(space, args):
    template = args[0]
    formatter = StringFormatter(template.str(), args[1:])
    printf_(formatter.format())
    return W_Null()


def print_r(space, args):
    array = args[0]
    assert(isinstance(array, W_Array))
    result = array.str_full()
    printf_(result)
    return W_Null()


def dechex(space, args):
    number = args[0]
    assert(isint(number))
    return W_StringObject(hex(number.get_int()))


def number_format(space, args):
    number = args[0]
    positions = args[1]
    assert(isint(positions))

    number = number.to_number()
    positions = positions.get_int()

    formatted = str(formatd(number, "f", positions))

    return W_StringObject(formatted)


def array_range(space, args):
    start = args[0]
    finish = args[1]
    assert(isint(start))
    assert(isint(finish))
    array = W_Array()
    i = 0
    for number in range(start.get_int(), finish.get_int()+1):
        array.put(W_IntObject(i), W_IntObject(number))
        i += 1
    return array


def gettimeofday(space, args):
    seconds = time.time()
    usec = int(seconds * 1000000) - int(seconds) * 1000000
    sec = int(seconds)

    array = W_Array()
    array.put(W_StringObject('sec'), W_IntObject(sec))
    array.put(W_StringObject('usec'), W_IntObject(usec))
    return array

# ----- #


def new_native_function(name, function, params=[]):
    func = NativeFunction(name, function)
    obj = W_CodeFunction(func)
    return obj

functions = [
    new_native_function('define', define),
    new_native_function('strlen', strlen),
    new_native_function('str_repeat', str_repeat),
    new_native_function('printf', printf),
    new_native_function('print_r', print_r),
    new_native_function('dechex', dechex),
    new_native_function('number_format', number_format),
    new_native_function('range', array_range),
    new_native_function('gettimeofday', gettimeofday),
]
