#from bottelo.run_python_code import run_python_code
from bottelo.irc import IrcBot
from bottelo.run_python_code import run_python_code


bot = IrcBot(
    host="localhost",
    port=6667,
    use_ssl=False,
    nick="bottelo",
    channels=["#a"],
)

@bot.command("!py3")
def py3(sender: str, recipient: str, code: str) -> str:
    return f"{sender}: {run_python_code(code)}"

bot.run_forever()
