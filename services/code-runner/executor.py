from __future__ import annotations

import logging
import os
import resource
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

MAX_OUTPUT = int(os.environ.get("CODE_EXECUTION_OUTPUT_LIMIT", "65536"))
DEFAULT_TIMEOUT = int(os.environ.get("CODE_EXECUTION_TIMEOUT", "5"))
MEMORY_MB = int(os.environ.get("CODE_EXECUTION_MEMORY_MB", "256"))


@dataclass
class RunResult:
    success: bool
    stdout: list[str]
    stderr: str
    execution_time_ms: int
    timed_out: bool = False
    compile_error: bool = False

    def as_dict(self) -> dict:
        return {
            "success": self.success,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "execution_time_ms": self.execution_time_ms,
            "timed_out": self.timed_out,
            "compile_error": self.compile_error,
        }


class LanguageSpec:
    name: str
    file_name: str

    def compile(self, workdir: Path) -> list[str] | None:
        return None

    def run(self, workdir: Path) -> list[str]:
        raise NotImplementedError


class JavaSpec(LanguageSpec):
    name = "java"
    file_name = "Main.java"

    def compile(self, workdir: Path) -> list[str] | None:
        return ["javac", self.file_name]

    def run(self, workdir: Path) -> list[str]:
        return ["java", "-Xmx128m", "Main"]


class PythonSpec(LanguageSpec):
    name = "python"
    file_name = "main.py"

    def run(self, workdir: Path) -> list[str]:
        return ["python3", "-I", self.file_name]


class JavaScriptSpec(LanguageSpec):
    name = "javascript"
    file_name = "main.js"

    def run(self, workdir: Path) -> list[str]:
        return ["node", "--no-experimental-fetch", self.file_name]


SPECS: dict[str, LanguageSpec] = {
    "java": JavaSpec(),
    "python": PythonSpec(),
    "javascript": JavaScriptSpec(),
    "js": JavaScriptSpec(),
}


def get_spec(language: str) -> LanguageSpec:
    spec = SPECS.get(language.lower())
    if spec is None:
        raise ValueError(f"Unsupported language: {language}")
    return spec


def _limit_resources() -> None:
    try:
        mem = MEMORY_MB * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (mem, mem))
        resource.setrlimit(resource.RLIMIT_CPU, (DEFAULT_TIMEOUT + 1, DEFAULT_TIMEOUT + 1))
        resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
        resource.setrlimit(resource.RLIMIT_NPROC, (32, 32))
        resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_OUTPUT * 4, MAX_OUTPUT * 4))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    except (ValueError, resource.error, OSError):
        pass


def _run(
    command: list[str],
    workdir: Path,
    timeout: int,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    safe_env = {
        "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        "HOME": str(workdir),
        "LANG": "C.UTF-8",
        "JAVA_TOOL_OPTIONS": "-Xmx128m",
    }
    if env:
        safe_env.update(env)
    return subprocess.run(
        command,
        cwd=workdir,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=safe_env,
        preexec_fn=_limit_resources if os.name == "posix" else None,
        check=False,
    )


def _split_output(raw: str) -> list[str]:
    clipped = raw[:MAX_OUTPUT]
    lines = clipped.replace("\r\n", "\n").split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    return lines


def execute(language: str, code: str, timeout: int | None = None) -> RunResult:
    spec = get_spec(language)
    timeout = timeout or DEFAULT_TIMEOUT
    started = time.perf_counter()
    workdir = Path(tempfile.mkdtemp(prefix="sandbox-"))
    try:
        os.chmod(workdir, 0o700)
        source = workdir / spec.file_name
        source.write_text(code, encoding="utf-8")

        compile_cmd = spec.compile(workdir)
        if compile_cmd:
            if shutil.which(compile_cmd[0]) is None:
                return RunResult(
                    success=False,
                    stdout=[],
                    stderr=f"{compile_cmd[0]} is not installed in the sandbox.",
                    execution_time_ms=int((time.perf_counter() - started) * 1000),
                    compile_error=True,
                )
            try:
                compiled = _run(compile_cmd, workdir, timeout)
            except subprocess.TimeoutExpired:
                return RunResult(
                    success=False,
                    stdout=[],
                    stderr="Compilation stopped because the program exceeded the time limit.",
                    execution_time_ms=int((time.perf_counter() - started) * 1000),
                    timed_out=True,
                    compile_error=True,
                )
            if compiled.returncode != 0:
                return RunResult(
                    success=False,
                    stdout=[],
                    stderr=(compiled.stderr or compiled.stdout or "Compilation Error")[:MAX_OUTPUT],
                    execution_time_ms=int((time.perf_counter() - started) * 1000),
                    compile_error=True,
                )

        run_cmd = spec.run(workdir)
        if shutil.which(run_cmd[0]) is None:
            return RunResult(
                success=False,
                stdout=[],
                stderr=f"{run_cmd[0]} is not installed in the sandbox.",
                execution_time_ms=int((time.perf_counter() - started) * 1000),
            )
        try:
            ran = _run(run_cmd, workdir, timeout)
        except subprocess.TimeoutExpired:
            return RunResult(
                success=False,
                stdout=[],
                stderr="Execution stopped because the program exceeded the time limit.",
                execution_time_ms=int((time.perf_counter() - started) * 1000),
                timed_out=True,
            )
        stdout = _split_output(ran.stdout or "")
        stderr = (ran.stderr or "")[:MAX_OUTPUT]
        return RunResult(
            success=ran.returncode == 0,
            stdout=stdout,
            stderr=stderr,
            execution_time_ms=int((time.perf_counter() - started) * 1000),
        )
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
