from app.services.run_help import parse_error_line


def test_parse_java_compiler_line() -> None:
    stderr = "Main.java:5: error: ';' expected\n    int x = 1\n            ^"
    assert parse_error_line("java", stderr) == 5


def test_parse_python_and_js_lines() -> None:
    python_err = 'File "main.py", line 4, in <module>\n    print(unknown)\nNameError: name \'unknown\' is not defined'
    assert parse_error_line("python", python_err) == 4
    js_err = "main.js:3\nconsole.log(missing);\n            ^\nReferenceError: missing is not defined"
    assert parse_error_line("javascript", js_err) == 3
