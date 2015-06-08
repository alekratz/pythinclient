__author__ = 'Alek Ratzloff <alekratz@gmail.com>'

from socket import socket


class ThinClient:
    """
    Python client used for doing stuff... Thinly
    """
    def __init__(self, port, host="127.0.0.1", recv_size=1024):
        self.port = port
        self.host = host
        self.recv_size = recv_size
        self.sock = None

    def connect(self):
        """
        Creates a connection from a thin client to a server to send commands back and forth.
        """
        if self.sock:
            raise Exception("Client is already connected to a server")
        # create the socket and connect
        self.sock = socket()
        self.sock.connect((self.host, self.port))

    def close(self):
        """
        Closes a connection from a thin client to a server.
        """
        self.__verify_connection()
        self.sock.close()
        self.sock = None

    def send(self, message):
        """
        Sends a message to the server after a connection is established.
        :param message: the message or command to send to the server
        """
        self.__verify_connection()
        # determine the type of the message; convert it to bytes if need be
        if type(message) is str:
            message = message.encode('ascii')
        self.sock.send(message)

    def wait_receive(self):
        """
        Blocks program execution until a message is received from the server.
        :return: the string read from the server
        """
        self.__verify_connection()
        return self.sock.recv(self.recv_size).decode('utf-8')

    def send_receive(self, message):
        """
        Creates a connection to the server, sends the message, waits on a
        response, closes the connection, and returns the server's response.
        """
        self.connect()
        self.send(message)
        response = self.wait_receive()
        self.close()
        return response

    def __verify_connection(self):
        """
        Ensures that the thin client is connected to a server. If not, it will raise an exception.
        """
        if not self.sock:
            raise Exception("Client is not connected to the server")


class BasicThinClient(ThinClient):
    def __init__(self, port=65000, host="127.0.0.1", recv_size=1024):
        super(BasicThinClient, self).__init__(port, host, recv_size)
