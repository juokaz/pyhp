
from pyhp.datatypes import isint, isfloat, isstr
from pyhp.objspace import w_Null, newint, newstring, new_native_function
from pyhp.datatypes import W_Array
from pyhp.utils import printf as printf_, StringFormatter

import time
from rpython.rlib.rfloat import formatd
from rpython.rlib.rarithmetic import intmask


def define(space, args):
    name = args[0].get_value()
    assert(isstr(name))
    value = args[1].get_value()
    space.declare_constant(name.str(), value)


def strlen(space, args):
    string = args[0].get_value()
    assert(isstr(string))
    return newint(string.len())


def str_repeat(space, args):
    string = args[0].get_value()
    repeat = args[1].get_value()
    assert(isstr(string))
    assert(isint(repeat))
    repeated = string.str() * repeat.get_int()
    return newstring(repeated)


def printf(space, args):
    template = args[0]
    assert(isstr(template))
    items = [arg.get_value() for arg in args[1:]]
    formatter = StringFormatter(template.str(), items)
    printf_(formatter.format())


def print_r(space, args):
    array = args[0].get_value()
    assert(isinstance(array, W_Array))
    result = array.str_full()
    printf_(result)
    return w_Null


def dechex(space, args):
    number = args[0].get_value()
    assert(isint(number))
    return newstring(hex(number.get_int()))


def number_format(space, args):
    number = args[0].get_value()
    assert(isfloat(number))
    positions = args[1].get_value()
    assert(isint(positions))

    number = number.to_number()
    positions = positions.get_int()

    formatted = str(formatd(number, "f", positions))

    return newstring(formatted)


def array_range(space, args):
    start = args[0].get_value()
    finish = args[1].get_value()
    assert(isint(start))
    assert(isint(finish))
    array = W_Array()
    i = 0
    for number in range(start.get_int(), finish.get_int()+1):
        array.put(newint(i), newint(number))
        i += 1
    return array


def gettimeofday(space, args):
    seconds = time.time()
    seconds = str(formatd(seconds, "f", 6))
    sec = int(seconds.split('.')[0])
    usec = int(seconds.split('.')[1])

    array = W_Array()
    array.put(newstring('sec'), newint(intmask(sec)))
    array.put(newstring('usec'), newint(intmask(usec)))
    return array

# ----- #

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
