from rpython.rlib import rsocket
from rpython.rlib.objectmodel import enforceargs


def open_socket(hostname, port):
    hostip = rsocket.gethostbyname(hostname)
    host = rsocket.INETAddress(hostip.get_host(), port)

    socket = rsocket.RSocket(rsocket.AF_INET, rsocket.SOCK_STREAM)
    socket.bind(host)
    socket.listen(1)

    return socket


def wait_for_connection(socket):
    (fd, client_addr) = socket.accept()

    client_sock = rsocket.fromfd(fd, rsocket.AF_INET, rsocket.SOCK_STREAM)

    return client_sock


@enforceargs(None, int)
def read_request(client_sock, buffer_size):
    if buffer_size < 0:
        raise Exception()
    msg = client_sock.recv(buffer_size)
    msg = msg.rstrip("\n")
    print "rcv: '%s'" % msg
    return msg


def return_response(client_sock, response):
    http_response = u"""HTTP/1.1 200 OK
Content-Type: text/html;charset=utf-8
Content-Length: %d

%s""" % (len(response), response)
    client_sock.send(http_response.encode('utf-8'))


def connection_close(client_sock):
    client_sock.close()
