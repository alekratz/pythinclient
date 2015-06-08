#!/usr/bin/env python3

from pythinclient.server import BasicThinServer

def server_help(msg, conn, addr):
  conn.send(
    """
    Available commands:
    help      : shows this help
    echo      : send a message back to the client
    log       : log a message to the server.log file
    """.encode('ascii'))

def server_echo(msg, conn, addr):
  conn.send((msg + '\n').encode('ascii'))

def server_log(msg, conn, addr):
  # write the given message to the logfile
  with open("server.log", "a+") as fp:
    fp.write(msg + '\n')

if __name__ == "__main__":
  from sys import argv
  daemon = True if "-d" in argv or "--daemon" in argv else False
  server = BasicThinServer(is_daemon=daemon)

  # add hooks
  server.add_hook('help', server_help)
  server.add_hook('echo', server_echo)
  server.add_hook('log', server_log)

  # start it up
  server.start()