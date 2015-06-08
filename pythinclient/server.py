__author__ = 'Alek Ratzloff <alekratz@gmail.com>'

import abc
from socket import socket
from os.path import exists
from os import fork
from threading import Thread


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
        self.child_pid = -1

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
                self.child_pid = child
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

    def on_receive(self, message, conn, addr):
        """
        Handles the receiving of a message from a client
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


class AsyncThinServer(ThinServer):
    def __init__(self, port=65000, host='127.0.0.1', recv_size=1024, is_daemon=False, lockfile="/tmp/pythinclient.pid"):
        super(AsyncThinServer, self).__init__(port, host, recv_size, is_daemon, lockfile)
        # Connections are indexed by their address tuples
        self.__connections = {}

    def on_accept(self, conn, addr):
        """
        Handles what happens when a connection is accepted to the thin server.
        :param conn: the socket connection that connected to the server
        :param addr: the address that connected to the server
        """
        assert (addr not in self.__connections)

        # create an asynchronous listener for this connection
        listener = AsyncListener(conn, addr, self)
        self.__connections[addr] = listener
        listener.start()

    def on_receive(self, message, conn, addr):
        # call the basic onreceive stuff
        super(AsyncThinServer, self).on_receive(message, conn, addr)
        # check to see if the listener is still alive; if not, remove it
        if not self.__connections[addr].alive:
            print("deleting connection from %s" % str(addr))
            del self.__connections[addr]
            print("%s connections to the server right now" % len(self.__connections))


class AsyncListener(Thread):
    def __init__(self, conn, addr, thin_server):
        """
        Initializes a single connection listener for a client.
        """
        super(AsyncListener, self).__init__()
        self.conn = conn
        self.addr = addr
        self.thin_server = thin_server
        self.alive = False

    def run(self):
        assert not self.alive
        self.__listen_loop()

    def __listen_loop(self):
        self.alive = True
        while self.alive:
            message = self.conn.recv(self.thin_server.recv_size)
            if len(message) == 0:
                self.alive = False
            self.thin_server.on_receive(message, self.conn, self.addr)
