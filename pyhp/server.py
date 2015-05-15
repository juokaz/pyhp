from rpython.rlib import rsocket

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

def read_request(client_sock, buffer_size=1024):
    msg = client_sock.recv(buffer_size)
    msg = msg.rstrip("\n")
    print "rcv: '%s'" % msg
    if msg == "":
        client_sock.close()
        return;
    return msg

def return_response(client_sock, response):
    http_response = """HTTP/1.1 200 OK
Content-Type: text/html;charset=utf-8
Content-Length: %d

%s""" % (len(response), response)
    client_sock.send(http_response)
    print 'sent: %s' % http_response
