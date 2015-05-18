from pyhp.interpreter import Interpreter
from pyhp.sourceparser import source_to_ast
from pyhp.bytecode import compile_ast

from rpython.rlib.streamio import open_file_as_stream
from rpython.rlib import rsocket
from rpython.rlib.objectmodel import enforceargs

import time
import os


class Request(object):
    def __init__(self, filename, get):
        self.filename = filename
        self.get = get


class Server(object):
    def __init__(self, root=''):
        self.root = root
        self.socket = None
        self.cached_files = {}

    def listen(self, port):
        self.socket = self.open_socket(port)

    def run(self):
        # each new run needs a a new interpreter
        intrepreter = Interpreter()

        client, client_addr = self.wait_for_connection()
        request = self.read_request(client, 1024)

        bytecode = self._bytecode(request.filename)

        if bytecode is None:
            response = u"<html><body><p>404: File not found</p></body></html>"
            code = 404
        else:
            response = intrepreter.run_return(bytecode)
            code = 200

        self.return_response(client, code, response)

        current_date = str(time.time())
        client_addr = '%s:%d' % (client_addr.get_host(),
                                 client_addr.get_port())
        print "[%s] %s [%d]: %s" % (current_date, client_addr, code,
                                    request.filename)

        self.connection_close(client)

    def _bytecode(self, filename):
        filename = os.path.abspath(self.root + filename)

        # bytecode cache based on the filename
        try:
            return self.cached_files[filename]
        except KeyError:
            data = self._read_file(filename)
            if data is None:
                return None

            ast = source_to_ast(data)
            bc = compile_ast(ast, ast.scope, unicode(filename))

            self.cached_files[filename] = bc

        return bc

    def _read_file(self, filename):
        try:
            f = open_file_as_stream(filename)
        except OSError:
            print 'File not found %s' % filename
            return None
        data = f.readall()
        f.close()
        return data

    def open_socket(self, port):
        host = rsocket.INETAddress('', port)

        socket = rsocket.RSocket(rsocket.AF_INET, rsocket.SOCK_STREAM)
        socket.setsockopt_int(rsocket.SOL_SOCKET, rsocket.SO_REUSEADDR, 1)

        socket.bind(host)
        socket.listen(1)

        return socket

    def wait_for_connection(self):
        (fd, client_addr) = self.socket.accept()

        client_sock = rsocket.fromfd(fd, rsocket.AF_INET, rsocket.SOCK_STREAM)

        return client_sock, client_addr

    @enforceargs(None, None, int)
    def read_request(self, client_sock, buffer_size):
        msg = client_sock.recv(buffer_size)
        request = msg.rstrip("\n")

        if request == "":
            raise Exception("Empty request")

        return self.parse_request(request)

    def parse_request(self, request):
        request_method = request.split(' ')[0]

        if (request_method == 'GET') | (request_method == 'HEAD'):
            file_requested = request.split(' ')
            file_requested = file_requested[1]

            file_requested = file_requested.split('?')
            if len(file_requested) == 1:
                query = {}
            else:
                query = self._unpack_query(file_requested[1])
            file_requested = file_requested[0]

            if (file_requested == '/'):
                file_requested = '/index.php'  # load index.php by default

            return Request(file_requested, query)
        else:
            raise Exception("Unknown HTTP request method: %s" % request_method)

    def return_response(self, client_sock, code, response):
        h = u''
        if code == 200:
            h = u'HTTP/1.1 200 OK\n'
        elif code == 404:
            h = u'HTTP/1.1 404 Not Found\n'

        h += u'Content-Type: text/html;charset=utf-8\n'
        h += u'Content-Length: %d\n' % len(response)
        h += u'Server: PyHP-Server\n'
        # signal that the conection wil be closed after complting the request
        h += u'Connection: close\n\n'

        http_response = h + response

        client_sock.send(http_response.encode('utf-8'))

    def connection_close(self, client_sock):
        client_sock.close()

    def shutdown(self, sig, dummy):
        """ This function shuts down the server. It's triggered
        by SIGINT signal """
        self.socket.shutdown(rsocket.SHUT_RDWR)

    def _unpack_query(self, query):
        vars = query.split("&")
        params = {}
        for var in vars:
            l = var.split("=", 1)
            if len(l) == 1:
                params[l[0]] = ""
            else:
                params[l[0]] = l[1]
        return params
