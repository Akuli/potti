# If you are obsessed with TDD, you'd probably call this an Integration Test

import subprocess
import sys
import socket

import pytest


@pytest.fixture
def bot_with_server():
    process = subprocess.Popen([sys.executable, "-m", "potti", "--launch-server"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    # Wait until bot has joined channel
    output = b""
    while b"End of /NAMES list." not in output:
        output += process.stdout.readline()

    yield
    process.kill()


@pytest.fixture
def client(bot_with_server):
    sock = socket.socket()
    sock.connect(('localhost', 6667))
    yield sock
    sock.close()


def test_integration(client):
    client.sendall(b'NICK client\r\nUSER client 0 * :client\r\nJOIN #autojoin\r\nPRIVMSG #autojoin :!py print(1 + 2)\r\n')

    client.settimeout(20)
    received = b""
    while b"PRIVMSG #autojoin :client: 3\r\n" not in received:
        received += client.recv(100)
