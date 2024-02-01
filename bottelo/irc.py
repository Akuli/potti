# TODO: SSL aka TLS

import socket
import ssl
import traceback
from typing import Union, TypeVar, Callable

import certifi


_Socket = Union[socket.socket, ssl.SSLSocket]


# This function was copied from my Mantaray project.
# If there's a problem with it, you probably need to update Mantaray too.
def create_connection(host: str, port: int, use_ssl: bool) -> _Socket:
    sock: _Socket

    if use_ssl:
        context = ssl.create_default_context(cafile=certifi.where())
        sock = context.wrap_socket(socket.socket(), server_hostname=host)
    else:
        sock = socket.socket()

    try:
        sock.settimeout(15)
        sock.connect((host, port))
    except (OSError, ssl.SSLError) as e:
        sock.close()
        raise e

    sock.settimeout(None)
    return sock


def split_line(line: str) -> list[str]:
    if " :" in line:
        first_args, last_arg = line.split(" :", maxsplit=1)
        return first_args.split() + [last_arg]
    else:
        return line.split()


_CommandT = TypeVar("_CommandT", bound=Callable[[str, str, str], str | None])


class IrcBot:

    def __init__(
        self,
        host: str,
        nick: str,
        channels: list[str],
        *,
        port: int = 6697,
        use_ssl: bool = True,
        user: str | None = None,
        realname: str | None = None,
    ) -> None:
        self.sock = create_connection(host, port, use_ssl)
        self.send(f"NICK {nick}")
        self.send(f"USER {user or nick} 0 * :{realname or nick}")
        self.channels = channels
        self.commands: list[tuple[str, Callable[[str, str, str], str | None]]] = []

    def send(self, line: str) -> None:
        print("send:", line)
        self.sock.sendall(line.encode("utf-8") + b"\r\n")

    def run_forever(self) -> None:
        recv_buffer = b""
        while True:
            recv_buffer += self.sock.recv(1024)
            *full_lines, recv_buffer = recv_buffer.split(b"\n")
            for line in full_lines:
                self.handle_line(line.decode("utf-8").rstrip("\r"))

    def handle_line(self, line: str) -> None:
        print("recv:", line)

        command_or_sender, *args = split_line(line)
        if command_or_sender.startswith(":"):
            if "@" in command_or_sender:
                sender_nick = command_or_sender.split("!")[0]
                self.handle_message_from_user(sender_nick, args[0], args[1:])
            else:
                self.handle_message_from_server(args)
        elif command_or_sender == "PING":
            if args:
                self.send(f"PONG :{args[1]}")
            else:
                # TODO: does this ever happen?
                self.send("PONG")

    def handle_message_from_server(self, args: list[str]) -> None:
        if args[0] == "376":
            # End of MOTD
            for chan in self.channels:
                self.send(f"JOIN {chan}")

    def handle_message_from_user(self, sender: str, kind: str, args: list[str]) -> None:
        if kind == "PRIVMSG":
            # Direct message (recipient is nick) or channel message (recipient is channel)
            recipient, message = args
            self.handle_privmsg(sender, recipient, message)

    def handle_privmsg(self, sender: str, recipient: str, message: str) -> None:
        for prefix, callback in self.commands:
            if message.startswith(f"{prefix} "):
                try:
                    response = callback(sender, recipient, message[len(prefix):].strip())
                except Exception:
                    traceback.print_exc()
                    response = "Error :("
                if response:
                    if recipient.startswith('#'):
                        # Send response to channel
                        self.send(f"PRIVMSG {recipient} :{response}")
                    else:
                        # Send response as DM/PM (Direct/Private Message)
                        self.send(f"PRIVMSG {sender} :{response}")

    def command(self, prefix: str) -> Callable[[_CommandT], _CommandT]:
        def actually_register(callback: _CommandT) -> _CommandT:
            self.commands.append((prefix, callback))
            return callback

        return actually_register
