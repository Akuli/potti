from potti.run_python_code import run


def test_succeeding_codes():
    assert run("'a' + 'b'") == 'ab'  # TODO: "'ab'" would be better
    assert run("1 + 2") == '3'
    assert run("[1] + [2]") == '[1, 2]'
    assert run("print(1 + 2)") == '3'
    assert run("3 + 4j") == '(3+4j)'
    assert run("print('x'); print('y'); 'z'") == 'x y z'


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
    output = run("while True: print('a')")
    assert 1000 <= len(output) <= 1100
    assert output.startswith('a a a a a a a a a a a a a a a ')

    output = run("while True: print('a', end='', flush=True)")
    assert 1000 <= len(output) <= 1100
    assert output.startswith('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
