#!/usr/bin/env python3

from pythinclient.client import BasicThinClient

if __name__ == "__main__":
  client = BasicThinClient(65000)
  running = True
  while running:
    try:
      line = input("> ")
    except (KeyboardInterrupt, EOFError):
      break
    if not bool(line.strip()): continue
    # process the line with the client
    try:
      # attempt to connect, send, receive, and close interactions with the server
      response = client.send_receive(line)
    except Exception as ex:
      response = "Could not make a connection to the server\n"
      response += "reason: %s" % ex
    print(response)