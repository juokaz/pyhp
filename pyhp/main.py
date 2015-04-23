from rpython.rlib.streamio import open_file_as_stream
from rpython.rlib.parsing.parsing import ParseError

from pyhp.interpreter import Frame, execute
from pyhp.sourceparser import _parse, ToAST, Transformer
from pyhp.bytecode import compile_ast
from pyhp.stdlib import stdlib

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


def bytecode(ast):
    """ Compile the AST into a bytecode
    """
    bc = compile_ast(ast, ast.scope)
    return bc


def interpret(bc):
    """ Interpret bytecode and execute it
    """
    frame = Frame(bc.symbols, stdlib)
    execute(frame, bc)
    return frame  # for tests and later introspection


def run(filename):
    f = open_file_as_stream(filename)
    data = f.readall()
    f.close()

    ast = parse(data)
    bc = bytecode(ast)
    interpret(bc)

    return 0
