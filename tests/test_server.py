from tests import TestBase
from pyhp.server import Server
from mock import patch, MagicMock

class TestServer(TestBase):
    @patch('rpython.rlib.rsocket.fromfd')
    @patch('rpython.rlib.rsocket.INETAddress')
    @patch('rpython.rlib.rsocket.RSocket')
    def test_running(self, socket_mock, inetaddress_mock, fromfd):
        inetaddress = inetaddress_mock.return_value

        bc = self.bytecode("""function a($x) {
            print $x;
        }
        $x = 1;
        print $x;""")
        server = Server(bc, 0)

        # socket init in open_socket()
        socket_mock.assert_called_with(2, 1)
        inetaddress_mock.assert_called_with('', 0)
        socket = socket_mock.return_value
        socket.bind.assert_called_with(inetaddress)

        # run in wait_for_connection()
        socket.accept.return_value = (1, 'addr')


        class ClientSocket(object):
            pass

        client_socket = ClientSocket()
        client_socket.recv = MagicMock(return_value='GET')
        client_socket.send = MagicMock()
        client_socket.close = MagicMock()
        fromfd.return_value = client_socket

        server.run()

        # client_socket instantiation in wait_for_connection()
        fromfd.assert_called_with(1, 2, 1)

        # response sent in return_response()
        client_socket.send.assert_called_with("""HTTP/1.1 200 OK
Content-Type: text/html;charset=utf-8
Content-Length: 1

1""")

        # close in connection_close()
        client_socket.close.assert_called_with()
