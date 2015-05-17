from pyhp.interpreter import Interpreter

from rpython.rlib import rsocket
from rpython.rlib.objectmodel import enforceargs


class Server(object):
    _immutable_fields_ = ['bytecode']

    def __init__(self, bytecode, port):
        from pyhp.bytecode import ByteCode
        assert(isinstance(bytecode, ByteCode))
        self.bytecode = bytecode
        self.socket = self.open_socket(port)

    def run(self):
        # each new run needs a a new interpreter
        intrepreter = Interpreter()

        client = self.wait_for_connection()
        request = self.read_request(client, 1024)
        if request != "":
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
        msg = msg.rstrip("\n")
        return msg

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
