from __future__ import annotations

import logging
import re
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
_JAVA_HOME: str | None = None
_JAVA_HOME_READY = False


def discover_java_home() -> str | None:
    """Find a real JDK. macOS /usr/bin/java is a stub without JAVA_HOME."""
    global _JAVA_HOME, _JAVA_HOME_READY
    if _JAVA_HOME_READY:
        return _JAVA_HOME
    _JAVA_HOME_READY = True
    env_home = (os.environ.get("JAVA_HOME") or "").strip()
    if env_home and (Path(env_home) / "bin" / "javac").exists():
        _JAVA_HOME = env_home
        return _JAVA_HOME
    java_home_tool = Path("/usr/libexec/java_home")
    if java_home_tool.exists():
        try:
            probed = subprocess.run(
                [str(java_home_tool)],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            home = (probed.stdout or "").strip().splitlines()
            if home and (Path(home[0]) / "bin" / "javac").exists():
                _JAVA_HOME = home[0]
                return _JAVA_HOME
        except Exception:
            logger.warning("java_home probe failed", exc_info=True)
    for candidate in (
        "/opt/java/openjdk",
        "/usr/lib/jvm/java-21-openjdk-amd64",
        "/usr/lib/jvm/java-17-openjdk-amd64",
        "/opt/homebrew/opt/openjdk",
        "/usr/local/opt/openjdk",
    ):
        if (Path(candidate) / "bin" / "javac").exists():
            _JAVA_HOME = candidate
            return _JAVA_HOME
    return None


def _resolve_bin(name: str) -> str | None:
    java_home = discover_java_home()
    if name in {"java", "javac"} and java_home:
        candidate = Path(java_home) / "bin" / name
        if candidate.exists():
            return str(candidate)
    return shutil.which(name)


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


def _needs_stdin(code: str) -> bool:
    lowered = code or ""
    return bool(
        re.search(r"\bScanner\s*\(", lowered)
        or re.search(r"System\.in\b", lowered)
        or re.search(r"\binput\s*\(", lowered)
        or re.search(r"readline\s*\(", lowered)
        or re.search(r"process\.stdin", lowered)
    )


def _demo_stdin(code: str) -> str:
    # One line is enough for nextLine()/input(); keep deterministic for thumbnails.
    if re.search(r"nextInt\s*\(|int\s*\(.*input", code or ""):
        return "7\n"
    return "Neha\n"


def _run(
    command: list[str],
    workdir: Path,
    timeout: int,
    env: dict[str, str] | None = None,
    stdin_data: str | None = None,
) -> subprocess.CompletedProcess[str]:
    java_home = discover_java_home()
    path_dirs = []
    if java_home:
        path_dirs.append(str(Path(java_home) / "bin"))
    path_dirs.extend(
        ["/usr/local/sbin", "/usr/local/bin", "/usr/sbin", "/usr/bin", "/sbin", "/bin"]
    )
    safe_env = {
        "PATH": ":".join(path_dirs),
        "HOME": str(workdir),
        "LANG": "C.UTF-8",
    }
    if java_home:
        safe_env["JAVA_HOME"] = java_home
    if env:
        safe_env.update(env)
    return subprocess.run(
        command,
        cwd=workdir,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=safe_env,
        input=stdin_data,
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
            tool = _resolve_bin(compile_cmd[0])
            if tool is None:
                return RunResult(
                    success=False,
                    stdout=[],
                    stderr=f"{compile_cmd[0]} is not installed in the sandbox.",
                    execution_time_ms=int((time.perf_counter() - started) * 1000),
                    compile_error=True,
                )
            compile_cmd = [tool, *compile_cmd[1:]]
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
        tool = _resolve_bin(run_cmd[0])
        if tool is None:
            return RunResult(
                success=False,
                stdout=[],
                stderr=f"{run_cmd[0]} is not installed in the sandbox.",
                execution_time_ms=int((time.perf_counter() - started) * 1000),
            )
        run_cmd = [tool, *run_cmd[1:]]
        stdin_data = _demo_stdin(code) if _needs_stdin(code) else None
        try:
            ran = _run(run_cmd, workdir, timeout, stdin_data=stdin_data)
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
