from executor import execute


def test_python_infinite_loop_times_out() -> None:
    result = execute("python", "while True:\n    pass\n", timeout=1)
    assert result.success is False
    assert result.timed_out is True
    assert "time limit" in result.stderr.lower()


def test_python_stdout() -> None:
    result = execute("python", "print(0)\nprint(1)\n", timeout=3)
    assert result.success is True
    assert result.stdout == ["0", "1"]
