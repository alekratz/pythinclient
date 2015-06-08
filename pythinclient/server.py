__author__ = 'Alek Ratzloff <alekratz@gmail.com>'

import abc
from socket import socket
from os.path import exists
from os import fork


class ThinServer:
    __metaclass__ = abc.ABCMeta

    def __init__(self, port, host='127.0.0.1', recv_size=1024, is_daemon=False, lockfile="/tmp/pythinclient.pid"):
        """
        Creates an instance of a server that listens for connections and commands from the thin client.
        :param port: the port to listen on
        :param host: the hostname to listen on. 127.0.0.1 by default
        :param recv_size: the size of the buffer to read. 1024 by default
        :param is_daemon: whether this thin server is a daemon. False by default
        :param lockfile: the file to use to hold the process ID of the daemon process
        """
        self.port = port
        self.host = host
        self.recv_size = recv_size
        self.sock = None
        self.is_daemon = is_daemon
        self.is_running = False
        self.lockfile = lockfile
        self.hooks = {}

    def start(self):
        assert ((self.sock is None) == (not self.is_running))

        self.is_running = True

        # determine if this is a daemonized server, and check to see if the lockfile is already taken
        if self.is_daemon:
            if exists(self.lockfile):
                raise Exception("Daemonized server is already running")
            # fork
            child = fork()
            if child == -1:
                raise Exception("Failed to fork for daemon")
            elif child == 0:
                # child section
                self.sock = socket()
                self.sock.bind((self.host, self.port))
                self.sock.listen(1)
                self._accept_loop()
            else:
                # parent section
                # create the lockfile and put the PID inside of it
                with open(self.lockfile, "w") as fp:
                    fp.write(str(child))
        else:
            # not a daemon. initialize like normal and run in this thread
            self.sock = socket()
            self.sock.bind((self.host, self.port))
            self.sock.listen(1)
            self._accept_loop()

    def add_hook(self, command, method):
        """
        Adds a keyword command for the server to invoke a method.
        The method must take 3 arguments: the message, the connection, and the address.
        :param command: the command, as a string, that is handled
        :param method: the function that is called
        :return:
        """
        self.hooks[command] = method

    def _accept_loop(self):
        """
        Private helper method that accepts clients
        :return:
        """
        assert self.sock
        assert self.is_running

        while self.is_running:
            conn, addr = self.sock.accept()
            self.on_accept(conn, addr)

    @abc.abstractmethod
    def on_accept(self, conn, addr):
        """
        Handles what happens when a connection is accepted to the thin server.
        :param conn: the socket connection that connected to the server
        :param addr: the address that connected to the server
        """
        return

    @abc.abstractmethod
    def on_receive(self, message, conn, addr):
        """
        Handles the receiving of a message from a client
        :param message: the message that was received
        :param conn: the socket connection that sent the message
        :param addr: the address of the connection that sent the message
        """
        return

class BasicThinServer(ThinServer):
    """
    A basic thin server that can be extended by adding method hooks. Check the add_hook method documentation on how to
    do so. This thin server can be used with the BasicThinClient.
    """
    def __init__(self, port=65000, host='127.0.0.1', recv_size=1024, is_daemon=False, lockfile="/tmp/pythinclient.pid"):
        super(BasicThinServer, self).__init__(port, host, recv_size, is_daemon, lockfile)

    def on_accept(self, conn, addr):
        """
        Handles what happens when a connection is accepted to the thin server.
        :param conn: the socket connection that connected to the server
        :param addr: the address that connected to the server
        """
        # receive the message
        message = conn.recv(self.recv_size)
        # handle the message
        self.on_receive(message, conn, addr)
        # close the connection
        conn.close()

    def on_receive(self, message, conn, addr):
        """
        Routes the received message to the correct handler
        :param message: the message that was received
        :param conn: the socket connection that sent the message
        :param addr: the address of the connection that sent the message
        """
        # if the message has a length of zero, break out
        if len(message) == 0:
            return
        # convert the message back to a string
        message = message.decode('utf-8')
        # get the first word of the message, and use that to figure out what the command was    
        command = message.split()[0]
        if command in self.hooks:
            try:
                self.hooks[command](message, conn, addr)
                result_message = b"OK"
            except Exception as ex:
                result_message = ("Server reported error: " + str(ex)).encode('ascii')
        else:
            result_message = b"Bad command"

        conn.send(result_message)
