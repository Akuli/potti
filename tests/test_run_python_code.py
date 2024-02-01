from bottelo.run_python_code import run_python_code


def test_run_python_code():
    assert run_python_code("'a' + 'b'") == 'ab'  # TODO: "'ab'" would be better
    assert run_python_code("1 + 2") == '3'
    assert run_python_code("print(1 + 2)") == '3'
    assert run_python_code("3 + 4j") == '(3+4j)'
    assert run_python_code("print('x'); print('y'); 'z'") == 'x y z'
