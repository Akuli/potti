from potti.run_python_code import run


def test_succeeding_codes():
    assert run("'a' + 'b'") == 'ab'  # TODO: "'ab'" would be better
    assert run("1 + 2") == '3'
    assert run("[1] + [2]") == '[1, 2]'
    assert run("print(1 + 2)") == '3'
    assert run("3 + 4j") == '(3+4j)'
    assert run("print('x'); print('y'); 'z'") == 'x y z'

    # Built-in module
    assert run("from math import cos, pi; cos(pi)") == "-1.0"

    # Standard-library module
    assert run("import logging; logging.getLogger('x').warning('test')") == "WARNING:x:test"


def test_errors():
    assert run("print('x'+1)") == 'TypeError: can only concatenate str (not "int") to str'


def test_dummy_fs():
    assert run('import os; sorted(os.listdir("/home"))') == "['pyodide', 'web_user']"
    assert run('import os; sorted(os.listdir("/home/pyodide"))') == "[]"
    assert run('import os; sorted(os.listdir("/home/web_user"))') == "[]"
    assert run('import os; len(os.listdir("/dev"))') == "9"


def test_memory_ddos_attack(monkeypatch):
    # Currently this times out on my system, but let's see what happens if we have faster CPU
    monkeypatch.setattr("potti.run_python_code.MAX_RUN_TIME", 10)
    assert run("print('a' * 1_000_000_000)") == "MemoryError"


def test_infinite_loop_ddos_attack():
    assert run("while True: pass") == "timed out"


def test_print_ddos_attack():
    # It strips a few spaces, and reads chunks of max 100 bytes until length 1000.
    min_len = 995
    max_len = 1100

    output = run("while True: print('a')")
    assert min_len <= len(output) <= max_len
    assert output.startswith('a a a a a a a a a a a a a a a ')

    output = run("while True: print('a', end='', flush=True)")
    assert min_len <= len(output) <= max_len
    assert output.startswith('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')


def test_escape_to_javascript_attack(monkeypatch):
    monkeypatch.setattr("potti.run_python_code.MAX_RUN_TIME", 10)

    # It is possible to run arbitrary javascript code, but it's useless because
    # of Deno's permissions: https://docs.deno.com/runtime/manual/basics/permissions
    def run_js(code):
        return run(f"import pyodide; pyodide.code.run_js({code!r})")

    assert run_js("Deno.readTextFile('/etc/hostname')") == (
        'PythonError: pyodide.ffi.JsException: PermissionDenied:'
        ' Requires read access to "/etc/hostname", run again with the --allow-read flag'
    )
    assert run_js("Deno.readDir('/home')").startswith(
        '[object Object] error: Uncaught (in promise) PermissionDenied: Requires read access to "/home"'
    )
    assert run_js("Deno.run({cmd: ['bash']})") == (
        'warning: Use of deprecated "Deno.run()" API. This API will be removed in Deno 2.'
        ' Run again with DENO_VERBOSE_WARNINGS=1 to get more details.'
        '  pyodide.ffi.JsException: PermissionDenied:'
        ' Requires run access to "bash", run again with the --allow-run flag'
    )


def test_no_network_access(monkeypatch):
    monkeypatch.setattr("potti.run_python_code.MAX_RUN_TIME", 10)

    # No access to plain old sockets. Libraries that use them don't work.
    assert run('import socket; socket.gethostname()') == 'emscripten'
    assert "OSError: [Errno 23] Host is unreachable" in run(
        'import socket; socket.create_connection(("google.com", 80))'
    )
    assert "OSError: [Errno 23] Host is unreachable" in run(
        'import socket; socket.create_connection(("127.0.0.1", 80))'
    )
    assert "OSError: [Errno 23] Host is unreachable" in run(
        'import urllib.request; urllib.request.urlopen("http://google.com/")'
    )
    assert "OSError: [Errno 23] Host is unreachable" in run(
        'import urllib.request; urllib.request.urlopen("http://127.0.0.1/")'
    )

    # If you try to use pyodide's custom thing, there's still permission issue
    assert run(
        'import pyodide.http; r = await pyodide.http.pyfetch("https://google.com/")'
    ) == (
        'OSError: Requires net access to "google.com", run again with the --allow-net flag'
    )
