from rpython.rlib.streamio import open_file_as_stream
from rpython.rlib.parsing.parsing import ParseError

from pyhp.interpreter import Frame, execute
from pyhp.sourceparser import _parse, ToAST, Transformer
from pyhp.bytecode import compile_ast
from pyhp.stdlib import scope as stdlibscope


def parse(source):
    """ Parse the source code and produce an AST
    """
    try:
        t = _parse(source)
    except ParseError, e:
        print e.nice_error_message(source=source)
        raise
    ast = ToAST().transform(t)
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
    frame = Frame(bc.symbols, None, stdlibscope)
    execute(frame, bc)
    return frame  # for tests and later introspection


def read_file(filename):
    f = open_file_as_stream(filename)
    data = f.readall()
    f.close()
    return data


def bytecode(filename):
    data = read_file(filename)
    ast = parse(data)
    bc = ast_to_bytecode(ast)
    return bc


def run(filename):
    bc = bytecode(filename)
    interpret(bc)

    return 0
