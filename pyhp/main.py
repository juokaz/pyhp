from rpython.rlib.streamio import open_file_as_stream
from rpython.rlib.parsing.parsing import ParseError

from pyhp.sourceparser import parse, Transformer
from pyhp.bytecode import compile_ast
from pyhp.interpreter import Interpreter

from pyhp.server import Server


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


def ast_to_bytecode(ast, filename):
    """ Compile the AST into a bytecode
    """
    last = filename.rfind('/') + 1
    assert last > 0
    filename = unicode(filename[last:])
    bc = compile_ast(ast, ast.scope, filename)
    return bc


def interpret(bc, return_output=False):
    """ Interpret bytecode and execute it
    """
    intrepreter = Interpreter()

    if return_output:
        return intrepreter.run_return(bc)
    else:
        intrepreter.run(bc)
        return None


def read_file(filename):
    f = open_file_as_stream(filename)
    data = f.readall()
    f.close()
    return data


def ast(filename):
    data = read_file(filename)
    ast = source_to_ast(data)
    return ast


def bytecode(filename):
    source = ast(filename)
    bc = ast_to_bytecode(source, filename)
    return bc


def run(filename):
    bc = bytecode(filename)
    interpret(bc)

    return 0


def run_return(filename):
    bc = bytecode(filename)
    return interpret(bc, True)


def main(argv):
    filename = None
    print_bytecode = False
    print_ast = False
    server = False
    server_port = 8080
    i = 1
    while i < len(argv):
        arg = argv[i]
        if arg.startswith('-'):
            if arg == '--bytecode':
                print_bytecode = True
            elif arg == '--ast':
                print_ast = True
            elif arg == '--server':
                if i == len(argv) - 1:
                    print "--server requires an int"
                    return 1
                try:
                    server_port = int(argv[i + 1])
                except ValueError:
                    print "--server requires an int"
                    return 1
                i += 1
                server = True
            else:
                print "Unknown parameter %s" % arg
                return 1
        else:
            filename = arg
            break
        i += 1

    if print_ast:
        print ast(filename).str()
        return 0
    elif print_bytecode:
        print bytecode(filename).str()
        return 0
    elif server:
        bc = bytecode(filename)
        server = Server(bc)
        try:
            server.listen(server_port)
        except Exception:
            print("Failed to acquire a socket for port %s " % server_port)
            return 1
        print 'Listening on http://localhost:%d\n' % (server_port,)
        while True:
            server.run()
        return 0
    else:
        return run(filename)
