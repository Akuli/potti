from bottelo.run_python_code import run_python_code


def test_succeeding_codes():
    assert run_python_code("'a' + 'b'") == 'ab'  # TODO: "'ab'" would be better
    assert run_python_code("1 + 2") == '3'
    assert run_python_code("[1] + [2]") == '[1, 2]'
    assert run_python_code("print(1 + 2)") == '3'
    assert run_python_code("3 + 4j") == '(3+4j)'
    assert run_python_code("print('x'); print('y'); 'z'") == 'x y z'


def test_errors():
    assert run_python_code("print('x'+1)") == 'TypeError: can only concatenate str (not "int") to str'


def test_dummy_fs():
    assert run_python_code('import os; sorted(os.listdir("/home"))') == "['pyodide', 'web_user']"
    assert run_python_code('import os; sorted(os.listdir("/home/pyodide"))') == "[]"
    assert run_python_code('import os; sorted(os.listdir("/home/web_user"))') == "[]"
    assert run_python_code('import os; len(os.listdir("/dev"))') == "9"
