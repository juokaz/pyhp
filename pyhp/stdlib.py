from pyhp.datatypes import isint, isfloat, isstr
from pyhp.objspace import new_native_function
from pyhp.utils import StringFormatter

import time
from rpython.rlib.rfloat import formatd


def define(interpreter, space, args):
    name = args[0].get_value()
    assert(isstr(name))
    value = args[1].get_value()

    if space.get_constant(name.str()):
        return space.w_False

    space.declare_constant(name.str(), value)
    return space.w_True


def strlen(interpreter, space, args):
    string = args[0].get_value()
    assert(isstr(string))
    return space.wrap(string.len())


def str_repeat(interpreter, space, args):
    string = args[0].get_value()
    repeat = args[1].get_value()
    assert(isstr(string))
    assert(isint(repeat))
    repeated = string.str() * repeat.get_int()
    return space.wrap(repeated)


def printf(interpreter, space, args):
    template = args[0]
    assert(isstr(template))
    items = [arg.get_value() for arg in args[1:]]
    formatter = StringFormatter(template.str(), items)
    interpreter.output(formatter.format())
    return space.w_Null


def print_r(interpreter, space, args):
    array = args[0].get_value()
    result = array.str_full()
    interpreter.output(result)
    return space.w_Null


def dechex(interpreter, space, args):
    number = args[0].get_value()
    assert(isint(number))
    return space.wrap(unicode(hex(number.get_int())))


def number_format(interpreter, space, args):
    number = args[0].get_value()
    assert(isfloat(number))
    positions = args[1].get_value()
    assert(isint(positions))

    number = number.to_number()
    positions = positions.get_int()

    return space.wrap(formatd(number, "f", positions))


def array_range(interpreter, space, args):
    start = args[0].get_value()
    finish = args[1].get_value()
    assert(isint(start))
    assert(isint(finish))
    array = [space.wrap(number) for number
             in range(start.get_int(), finish.get_int()+1)]
    return space.wrap(array)


def gettimeofday(interpreter, space, args):
    seconds = time.time()
    seconds = str(formatd(seconds, "f", 6))
    sec = int(seconds.split('.')[0])
    usec = int(seconds.split('.')[1])

    return space.newdictarray({
        u'sec': space.wrap(sec),
        u'usec': space.wrap(usec)
    })


def ob_start(interpreter, space, args):
    interpreter.start_buffering()
    return space.w_Null


def ob_end_clean(interpreter, space, args):
    interpreter.end_buffer()
    return space.w_Null


def ob_flush(interpreter, space, args):
    buffer = interpreter.end_buffer()
    interpreter.output(buffer)
    return space.w_Null


# ----- #

functions_ = [
    new_native_function(u'define', define, ['str']),
    new_native_function(u'strlen', strlen, ['str']),
    new_native_function(u'str_repeat', str_repeat, ['str', 'int']),
    new_native_function(u'printf', printf),
    new_native_function(u'print_r', print_r, ['array']),
    new_native_function(u'dechex', dechex, ['int']),
    new_native_function(u'number_format', number_format, ['float', 'int']),
    new_native_function(u'range', array_range, ['int', 'int']),
    new_native_function(u'gettimeofday', gettimeofday),
    new_native_function(u'ob_start', ob_start),
    new_native_function(u'ob_end_clean', ob_end_clean),
    new_native_function(u'ob_flush', ob_flush),
]

functions = {}
for function in functions_:
    functions[function.name] = function
