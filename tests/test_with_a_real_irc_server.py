# Integration Test, sounds fancy :)

import subprocess
import time
import sys
import socket

import pytest


@pytest.fixture
def server():
    process = subprocess.Popen([sys.executable, "server.py"], cwd="MantaTail")

    # Wait for server to start
    time.sleep(1)

    yield
    process.kill()


@pytest.fixture
def bot(server):
    process = subprocess.Popen([sys.executable, "-m", "potti"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    # Wait until bot has joined channel
    output = b""
    while b"End of /NAMES list." not in output:
        output += process.stdout.readline()

    yield
    process.kill()


@pytest.fixture
def client(server):
    sock = socket.socket()
    sock.connect(('localhost', 6667))
    yield sock
    sock.close()


def test_integration(server, bot, client):
    client = socket.socket()
    client.connect(('localhost', 6667))

    client.sendall(b'NICK client\r\nUSER client 0 * :client\r\nJOIN #a\r\nPRIVMSG #a :!py print(1 + 2)\r\n')

    client.settimeout(20)
    received = b""
    while b"PRIVMSG #a :client: 3\r\n" not in received:
        received += client.recv(100)
