from rpython.rlib.streamio import open_file_as_stream
from rpython.rlib.parsing.parsing import ParseError

from pyhp.frame import GlobalFrame
from pyhp.sourceparser import parse, Transformer
from pyhp.bytecode import compile_ast
from pyhp.stdlib import functions as global_functions
from pyhp.functions import GlobalCode
from pyhp.objspace import ObjectSpace


def source_to_ast(source):
    """ Parse the source code and produce an AST
    """
    try:
        ast = parse(source)
    except ParseError, e:
        print e.nice_error_message(source=source)
        raise
    transformer = Transformer()
    return transformer.dispatch(ast)


def ast_to_bytecode(ast):
    """ Compile the AST into a bytecode
    """
    bc = compile_ast(ast, ast.scope)
    return bc


def interpret(bc):
    """ Interpret bytecode and execute it
    """
    space = ObjectSpace(global_functions)
    code = GlobalCode(bc)
    frame = GlobalFrame(space, code)
    code.run(frame)
    return frame  # for tests and later introspection


def read_file(filename):
    f = open_file_as_stream(filename)
    data = f.readall()
    f.close()
    return data


def bytecode(filename):
    data = read_file(filename)
    ast = source_to_ast(data)
    bc = ast_to_bytecode(ast)
    return bc


def run(filename):
    bc = bytecode(filename)
    interpret(bc)

    return 0


def main(argv):
    filename = None
    print_bytecode = False
    i = 1
    while i < len(argv):
        arg = argv[i]
        if arg.startswith('-'):
            if arg == '--bytecode':
                print_bytecode = True
            else:
                print "Unknown parameter %s" % arg
                return 1
        else:
            filename = arg
            break
        i += 1

    if print_bytecode:
        print bytecode(filename)
        return 0
    else:
        return run(filename)
