# Potti

Potti is an IRC bot that lets users run Python code on it.

![screenshot1](screenshot-basic.png)

The Python code is executed securely but ridiculously
by using [a javascript runtime](https://deno.com/)
to run [Pyodide, a Python interpreter compiled as WebAssembly](https://pyodide.org/).
Pyodide naturally has no access to a real file system, because it's meant to be ran in a web browser.
Instead, it creates a fake file system and
crashes with various funny errors when you try to access real operating system functionality.

![screenshot2](screenshot-denied.png)


## Setup

Development setup:

```
$ python3 - m venv env
$ source env/bin/activate
$ pip install -r requirements-dev.txt
$ ./download-deno.sh
```

Running the bot: (you probably want to modify `potti/__main__.py` to suit your needs)

```
$ python3 -m potti 
```

Tests and type checking:

```
$ python3 -m pytest
$ mypy potti
```
