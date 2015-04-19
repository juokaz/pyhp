from rpython.rlib.streamio import open_file_as_stream
from pyhp.interpreter import interpret


def main(argv):
    filename = argv[1]
    f = open_file_as_stream(filename)
    data = f.readall()
    f.close()
    interpret(data)
    return 0
