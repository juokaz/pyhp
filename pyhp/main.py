from rpython.rlib.streamio import open_file_as_stream

from pyhp.sourceparser import source_to_ast
from pyhp.bytecode import compile_ast
from pyhp.interpreter import Interpreter

from pyhp.server import Server
import os


def ast_to_bytecode(ast, filename):
    """ Compile the AST into a bytecode
    """
    filename = unicode(os.path.abspath(filename))
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
    if filename is None:
        raise OSError("invalid filename")
    f = open_file_as_stream(filename)
    data = f.readall()
    f.close()
    return data


def ast(source):
    ast = source_to_ast(source)
    return ast


def bytecode(filename, source):
    source = ast(source)
    bc = ast_to_bytecode(source, filename)
    return bc


def run(filename, source):
    bc = bytecode(filename, source)
    interpret(bc)

    return 0


def run_return(filename, source):
    bc = bytecode(filename, source)
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

    source = ''
    if filename is not None or server is False:
        try:
            source = read_file(filename)
        except OSError:
            print 'File not found %s' % filename
            return 1

    if print_ast:
        print ast(source).str()
        return 0
    elif print_bytecode:
        print bytecode(filename, source).str()
        return 0
    elif server:
        server = Server(os.getcwd())
        try:
            server.listen(server_port)
        except Exception:
            print("Failed to acquire a socket for port %s " % server_port)
            return 1
        print 'Listening on http://localhost:%d' % (server_port,)
        print 'Document root is %s' % server.root
        print 'Press Ctrl-C to quit.'
        while True:
            server.run()
        return 0
    else:
        return run(filename, source)
