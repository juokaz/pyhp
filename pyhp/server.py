from pyhp.interpreter import Interpreter

from rpython.rlib import rsocket
from rpython.rlib.objectmodel import enforceargs


class Request(object):
    def __init__(self, filename, get):
        self.filename = filename
        self.get = get


class Server(object):
    _immutable_fields_ = ['bytecode']

    def __init__(self, bytecode):
        self.bytecode = bytecode
        self.socket = None

    def listen(self, port):
        self.socket = self.open_socket(port)

    def run(self):
        # each new run needs a a new interpreter
        intrepreter = Interpreter()

        client = self.wait_for_connection()
        request = self.read_request(client, 1024)

        # bytecode object name can be a function name or a filename, in unicode
        if request.filename != self.bytecode.name.encode('utf-8'):
            raise Exception("Requested %s, had %s bytecode" % (
                request.filename, self.bytecode.name.encode('utf-8')
            ))

        response = intrepreter.run_return(self.bytecode)
        self.return_response(client, response)

        self.connection_close(client)

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

        return client_sock

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

    def return_response(self, client_sock, response):
        http_response = u"""HTTP/1.1 200 OK
Content-Type: text/html;charset=utf-8
Content-Length: %d

%s""" % (len(response), response)
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
