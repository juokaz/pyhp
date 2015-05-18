
from pyhp.datatypes import isint, isfloat, isstr
from pyhp.objspace import w_Null, newint, newstring, w_True, w_False, \
    new_native_function
from pyhp.datatypes import W_Array
from pyhp.utils import StringFormatter

import time
from rpython.rlib.rfloat import formatd
from rpython.rlib.rarithmetic import intmask


def define(interpreter, args):
    name = args[0].get_value()
    assert(isstr(name))
    value = args[1].get_value()

    if interpreter.get_constant(name.str()):
        return w_False

    interpreter.declare_constant(name.str(), value)
    return w_True


def strlen(interpreter, args):
    string = args[0].get_value()
    assert(isstr(string))
    return newint(string.len())


def str_repeat(interpreter, args):
    string = args[0].get_value()
    repeat = args[1].get_value()
    assert(isstr(string))
    assert(isint(repeat))
    repeated = string.str() * repeat.get_int()
    return newstring(repeated)


def printf(interpreter, args):
    template = args[0]
    assert(isstr(template))
    items = [arg.get_value() for arg in args[1:]]
    formatter = StringFormatter(template.str(), items)
    interpreter.output(formatter.format())
    return w_Null


def print_r(interpreter, args):
    array = args[0].get_value()
    assert(isinstance(array, W_Array))
    result = array.str_full()
    interpreter.output(result)
    return w_Null


def dechex(interpreter, args):
    number = args[0].get_value()
    assert(isint(number))
    return newstring(unicode(hex(number.get_int())))


def number_format(interpreter, args):
    number = args[0].get_value()
    assert(isfloat(number))
    positions = args[1].get_value()
    assert(isint(positions))

    number = number.to_number()
    positions = positions.get_int()

    formatted = unicode(formatd(number, "f", positions))

    return newstring(formatted)


def array_range(interpreter, args):
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


def gettimeofday(interpreter, args):
    seconds = time.time()
    seconds = str(formatd(seconds, "f", 6))
    sec = int(seconds.split('.')[0])
    usec = int(seconds.split('.')[1])

    array = W_Array()
    array.put(newstring(u'sec'), newint(intmask(sec)))
    array.put(newstring(u'usec'), newint(intmask(usec)))
    return array


def ob_start(interpreter, args):
    interpreter.start_buffering()
    return w_Null


def ob_end_clean(interpreter, args):
    interpreter.end_buffer()
    return w_Null


def ob_flush(interpreter, args):
    buffer = interpreter.end_buffer()
    interpreter.output(buffer)
    return w_Null


# ----- #

functions = {
    u'define': new_native_function(u'define', define),
    u'strlen': new_native_function(u'strlen', strlen),
    u'str_repeat': new_native_function(u'str_repeat', str_repeat),
    u'printf': new_native_function(u'printf', printf),
    u'print_r': new_native_function(u'print_r', print_r),
    u'dechex': new_native_function(u'dechex', dechex),
    u'number_format': new_native_function(u'number_format', number_format),
    u'range': new_native_function(u'range', array_range),
    u'gettimeofday': new_native_function(u'gettimeofday', gettimeofday),
    u'ob_start': new_native_function(u'ob_start', ob_start),
    u'ob_end_clean': new_native_function(u'ob_end_clean', ob_end_clean),
    u'ob_flush': new_native_function(u'ob_flush', ob_flush),
}
