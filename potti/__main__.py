import argparse
import logging
import os
import re
import subprocess
import sys
import socket

from potti.irc import IrcBot
from potti import run_python_code


def start_mantaray() -> subprocess.Popen[bytes]:
    if not os.path.isfile("mantaray/mantaray/__main__.py"):
        raise RuntimeError("you need to run 'git submodule update --init'")
    return subprocess.Popen([sys.executable, "-m", "mantaray", "--bob"], cwd="mantaray")


def start_mantatail() -> subprocess.Popen[bytes]:
    if not os.path.isfile("MantaTail/server.py"):
        raise RuntimeError("you need to run 'git submodule update --init'")

    process = subprocess.Popen([sys.executable, "server.py"], cwd="MantaTail")

    # Wait for server to start
    while True:
        try:
            socket.create_connection(('localhost', 6667)).close()
            break
        except OSError:
            pass

    # Must be still running
    assert process.poll() is None
    return process


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

parser = argparse.ArgumentParser(prog="python3 -m potti")
parser.add_argument("--launch-server", action="store_true", help="whether to run Mantaray (GUI)")
parser.add_argument("--launch-client", action="store_true", help="whether to run MantaTail (local server)")
parser.add_argument("--prod", action="store_true", help="connect to Libera, not locally")
args = parser.parse_args()
assert not (args.prod and (args.launch_server or args.launch_client))

server_process = start_mantatail() if args.launch_server else None
client_process = start_mantaray() if args.launch_client else None

bot = IrcBot(
    host="irc.libera.chat" if args.prod else "localhost",
    use_ssl=args.prod,
    nick="potti",
    channels=["##learnpython", "##learnmath"] if args.prod else ["#autojoin"],
    realname="https://github.com/Akuli/potti",
)


@bot.command(r"!py (.*)")
def py_command(sender: str, recipient: str, match: re.Match[str]) -> str:
    code = match.group(1)
    try:
        output = run_python_code.run(code)
        if len(output) > 200:
            output = output[:200] + " [output truncated]"
    except Exception:
        log.exception(f"running code failed: {code!r}")
        output = "error :("
    return f"{sender}: {output}"


@bot.command(r"(hello|hi+)[ ,]+potti\b.*")
@bot.command(r"potti[:,] *(hello|hi+)\b.*")
def hello_command(sender: str, recipient: str, match: re.Match[str]) -> str:
    """Respond to greetings.

    Examples of recognized greetings:

        potti: hiiiiiii :)
        hello potti !!!
        hello potti :D
    """
    return f"Hello {sender} :)"


@bot.command(r"potti[:,].*")
def unknown_message_for_me_handler(sender: str, recipient: str, match: re.Match[str]) -> str:
    """Reply to unknown messages directed at the bot with beep boop."""
    return f"{sender}: I am a bot. Beep boop."


try:
    if client_process is None:
        bot.run_forever()
    else:
        # stop when mantaray window is closed
        bot.run_while(lambda: client_process.poll() is None)  # type: ignore
finally:
    if server_process is not None:
        server_process.kill()
    if client_process is not None:
        client_process.kill()
