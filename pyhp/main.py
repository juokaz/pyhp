from rpython.rlib.streamio import open_file_as_stream
from rpython.rlib.parsing.parsing import ParseError

from pyhp.frame import Frame, VarMap
from pyhp.sourceparser import parse, Transformer
from pyhp.bytecode import compile_ast
from pyhp.stdlib import scope as stdlibscope


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
    varmap = VarMap(bc.symbols)
    frame = Frame(varmap, stdlibscope)
    bc.execute(frame)
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
