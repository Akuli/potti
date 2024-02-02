import logging

from potti.irc import IrcBot
from potti.run_python_code import run_python_code


logging.basicConfig(level=logging.DEBUG)

log = logging.getLogger(__name__)


bot = IrcBot(
    host="localhost",
    port=6667,
    use_ssl=False,
    nick="potti",
    channels=["#a"],
)


@bot.command("!py")
def py3(sender: str, recipient: str, code: str) -> str:
    try:
        output = run_python_code(code)
        if len(output) > 200:
            output = output[:200] + " [output truncated]"
    except Exception:
        log.exception(f"running code failed: {code!r}")
        output = "error :("
    return f"{sender}: {output}"


bot.run_forever()
