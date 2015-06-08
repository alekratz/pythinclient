from unittest import TestCase
from pythinclient.client import *
from pythinclient.server import *
import time


__author__ = 'Alek Ratzloff <alekratz@gmail.com>'

DATEFMT = "%d/%m/%Y"
def today():
    return time.strftime(DATEFMT)

def server_echo(msg, conn, addr):
    # Echoes the message
    conn.send((msg + '\n').encode('ascii'))

def server_date(msg, conn, addr):
    # Sends the current date
    date = today()
    conn.send((date + '\n').encode('ascii'))

class TestThinClient(TestCase):
    def __init__(self, method_name):
        super(TestThinClient, self).__init__(method_name)
        # This is the server that we connect to
        self.server = BasicThinServer()
        # This is the client that connects to the server
        self.client = BasicThinClient()
        # Add some basic hooks for the server to handle
        self.server.add_hook("echo", server_echo)
        self.server.add_hook("date", server_date)
        self.server.start()

    def test_client_connect(self):
        self.client.connect()
        self.assertTrue(self.client.sock is not None)
        self.client.close()
        self.assertTrue(self.client.sock is None)

    def test_client_send_receive(self):
        now = today()
        # Basic send and receive
        self.client.connect()
        self.client.send("echo test")
        response = self.client.wait_receive()
        self.assertEqual(response, "echo test")
        self.client.close()

        self.client.connect()
        self.client.send("date")
        response = self.client.wait_receive()
        self.assertEqual(response, now)
        self.client.close()

        # One line send and receive
        response = self.client.send_receive("echo test")
        self.assertEqual(response, "echo test")
        response = self.client.send_receive("date")
        self.assertEqual(response, now)