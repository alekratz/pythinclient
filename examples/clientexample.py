#!/usr/bin/env python3

from pythinclient.client import BasicThinClient

if __name__ == "__main__":
  client = BasicThinClient(65000)
  running = True
  while running:
    line = input("> ")
    if line == "": continue
    # process the line with the client
    try:
      client.connect()
      client.send(line)
      # wait for a response from the server
      response = client.wait_receive().decode('utf-8')
      client.close()
    except Exception as ex:
      response = "Could not make a connection to the server\n"
      response += "reason: %s" % ex
    print(response)