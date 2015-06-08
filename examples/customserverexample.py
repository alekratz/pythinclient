#!/usr/bin/env python3

from pythinclient.server import ThinServer

class CustomThinServer(BasicThinServer):
  def __init__(self, port=65000, is_daemon=False):
    super(BasicThinServer, self).__init__(port, is_daemon=is_daemon)
    # add custom server hooks
    self.add_hook('help', self.__server_help)
    self.add_hook('echo', self.__server_echo)
    self.add_hook('log', self.__server_log)

  def on_accept(self, conn, addr):
    """
    This is basically a copy of the on_accept from the BasicThinServer
    """
    # receive the message
    message = conn.recv(self.recv_size)
    # handle the message
    self.on_receive(message, conn, addr)
    # close the connection
    conn.close()

  def __server_help(self, msg, conn, addr):
    conn.send(
      """
      Available commands:
      help      : shows this help
      echo      : send a message back to the client
      log       : log a message to the server.log file
      """.encode('ascii'))

  def __server_echo(self, msg, conn, addr):
    conn.send((msg + '\n').encode('ascii'))

  def __server_log(self, msg, conn, addr):
    # write the given message to the logfile
    with open("server.log", "a+") as fp:
      fp.write(msg + '\n')

if __name__ == "__main__":
  from sys import argv
  daemon = True if "-d" in argv or "--daemon" in argv else False
  server = CustomThinServer(is_daemon=daemon)

  # start it up
  server.start()