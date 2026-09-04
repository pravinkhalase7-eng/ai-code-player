from __future__ import annotations

import shutil
import subprocess

import pytest

from executor import execute

JAVA_FOR = """public class Main {
    public static void main(String[] args) {
        for (int i = 0; i < 5; i++) {
            System.out.println(i);
        }
    }
}
"""

INFINITE = """public class Main {
    public static void main(String[] args) {
        for (int i = 0; i < 5; ) {
            System.out.println(i);
        }
    }
}
"""

BAD = """public class Main {
    public static void main(String[] args) {
        for (int i = 0; i < 5; i++) {
            System.out.println(i)
        }
    }
}
"""


def _java_runtime_available() -> bool:
    if shutil.which("javac") is None or shutil.which("java") is None:
        return False
    probe = subprocess.run(["java", "-version"], capture_output=True, text=True, timeout=5, check=False)
    text = (probe.stderr or probe.stdout or "").lower()
    return probe.returncode == 0 and "unable to locate a java runtime" not in text


pytestmark = pytest.mark.skipif(not _java_runtime_available(), reason="Java runtime is required")


def test_java_for_loop_stdout() -> None:
    result = execute("java", JAVA_FOR, timeout=8)
    assert result.success is True
    assert result.stdout == ["0", "1", "2", "3", "4"]
    assert result.stderr == ""


def test_java_compile_error() -> None:
    result = execute("java", BAD, timeout=8)
    assert result.success is False
    assert result.compile_error is True
    assert result.stderr


def test_infinite_loop_times_out() -> None:
    result = execute("java", INFINITE, timeout=2)
    assert result.success is False
    assert result.timed_out is True
    assert "time limit" in result.stderr.lower()
