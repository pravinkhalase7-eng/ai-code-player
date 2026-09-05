from __future__ import annotations

import logging
import re
from typing import Any

from app.schemas.lesson import ExecutionStep, VariableSnapshot

logger = logging.getLogger(__name__)

FOR_LOOP_RE = re.compile(
    r"for\s*\(\s*(?:(?:int|let|const|var)\s+)?(?P<var>[A-Za-z_]\w*)\s*=\s*(?P<start>-?\d+)\s*;"
    r"\s*(?P=var)\s*(?P<op><=|<|>=|>)\s*(?P<end>-?\d+)\s*;"
    r"\s*(?P=var)\s*(?P<inc>\+\+|--|\+=\s*\d+|-=\s*\d+)\s*\)",
    re.MULTILINE,
)
PY_FOR_RE = re.compile(
    r"for\s+(?P<var>[A-Za-z_]\w*)\s+in\s+range\(\s*(?P<args>[^)]*)\s*\)",
    re.MULTILINE,
)


def _next_value(value: int, inc: str) -> int:
    token = inc.replace(" ", "")
    if token == "++":
        return value + 1
    if token == "--":
        return value - 1
    if token.startswith("+="):
        return value + int(token[2:])
    if token.startswith("-="):
        return value - int(token[2:])
    return value + 1


def _compare(value: int, op: str, end: int) -> bool:
    if op == "<":
        return value < end
    if op == "<=":
        return value <= end
    if op == ">":
        return value > end
    if op == ">=":
        return value >= end
    return False


def source_filename(language: str) -> str:
    name = (language or "java").lower()
    if name == "python":
        return "main.py"
    if name in {"javascript", "js"}:
        return "main.js"
    return "Main.java"


def run_command(language: str) -> str:
    name = (language or "java").lower()
    if name == "python":
        return "python3 main.py"
    if name in {"javascript", "js"}:
        return "node main.js"
    return "javac Main.java && java Main"


def normalize_language(language: str) -> str:
    name = (language or "java").strip().lower()
    if name in {"js", "node", "nodejs"}:
        return "javascript"
    if name in {"py", "python3"}:
        return "python"
    if name in {"java", "python", "javascript"}:
        return name
    return "java"


_PUBLIC_CLASS = re.compile(r"public\s+class\s+([A-Za-z_]\w*)")


def ensure_runnable(language: str, code: str) -> str:
    """Make Java snippets runnable in Main.java without changing the student's idea."""
    if normalize_language(language) != "java":
        return code
    source = code.replace("\r\n", "\n")
    match = _PUBLIC_CLASS.search(source)
    if match and match.group(1) != "Main":
        source = _PUBLIC_CLASS.sub("public class Main", source, count=1)
    if "class " not in source:
        body = "\n".join(
            f"        {line}" if line.strip() else line
            for line in source.strip().splitlines()
        )
        source = (
            "public class Main {\n"
            "    public static void main(String[] args) {\n"
            f"{body}\n"
            "    }\n"
            "}\n"
        )
    return source


def _print_line(code: str, fallback: int = 4) -> int:
    for index, line in enumerate(code.splitlines(), start=1):
        lowered = line.lower()
        if "system.out" in line or "console.log" in lowered or "print(" in lowered:
            return index
    return fallback


def visualize_java_for_loop(code: str, stdout: list[str] | None = None) -> list[ExecutionStep]:
    return _visualize_c_style(code, stdout)


def _visualize_c_style(code: str, stdout: list[str] | None = None) -> list[ExecutionStep]:
    match = FOR_LOOP_RE.search(code)
    if not match:
        return []

    var = match.group("var")
    start = int(match.group("start"))
    op = match.group("op")
    end = int(match.group("end"))
    inc = match.group("inc")
    body_line = _print_line(code)

    steps: list[ExecutionStep] = []
    value = start
    index = 1
    output_index = 0
    steps.append(
        ExecutionStep(
            index=index,
            label=f"STEP {index}",
            description=f"Initialize {var} = {value}",
            line=max(1, body_line - 1),
            variables=[VariableSnapshot(name=var, value=str(value))],
        )
    )
    index += 1

    guard = 0
    while guard < 64:
        guard += 1
        passed = _compare(value, op, end)
        steps.append(
            ExecutionStep(
                index=index,
                label=f"STEP {index}",
                description=f"{value} {op} {end} → {'TRUE' if passed else 'FALSE'}",
                line=max(1, body_line - 1),
                condition=f"{var} {op} {end}",
                condition_result=passed,
                variables=[VariableSnapshot(name=var, value=str(value))],
                stopped=not passed,
            )
        )
        index += 1
        if not passed:
            break
        printed = None
        if stdout and output_index < len(stdout):
            printed = stdout[output_index]
            output_index += 1
        else:
            printed = str(value)
        steps.append(
            ExecutionStep(
                index=index,
                label=f"STEP {index}",
                description=f"print {printed}",
                line=body_line,
                output_line=printed,
                variables=[VariableSnapshot(name=var, value=str(value))],
            )
        )
        index += 1
        value = _next_value(value, inc)
        steps.append(
            ExecutionStep(
                index=index,
                label=f"STEP {index}",
                description=f"{var}++ → {var} = {value}" if "++" in inc else f"{var} becomes {value}",
                line=max(1, body_line - 1),
                variables=[VariableSnapshot(name=var, value=str(value))],
            )
        )
        index += 1
    return steps


def _range_values(args: str) -> list[int]:
    parts = [part.strip() for part in args.split(",") if part.strip()]
    nums = [int(part) for part in parts if re.fullmatch(r"-?\d+", part)]
    if len(nums) == 1:
        start, stop, step = 0, nums[0], 1
    elif len(nums) == 2:
        start, stop, step = nums[0], nums[1], 1
    elif len(nums) >= 3:
        start, stop, step = nums[0], nums[1], nums[2]
    else:
        return []
    if step == 0:
        return []
    values: list[int] = []
    current = start
    while len(values) < 32:
        if step > 0 and current >= stop:
            break
        if step < 0 and current <= stop:
            break
        values.append(current)
        current += step
    return values


def _visualize_python_range(code: str, stdout: list[str] | None = None) -> list[ExecutionStep]:
    match = PY_FOR_RE.search(code)
    if not match:
        return []
    var = match.group("var")
    values = _range_values(match.group("args"))
    if not values:
        return []
    body_line = _print_line(code)
    steps: list[ExecutionStep] = []
    index = 1
    output_index = 0
    for value in values:
        steps.append(
            ExecutionStep(
                index=index,
                label=f"STEP {index}",
                description=f"{var} = {value}",
                line=max(1, body_line - 1),
                variables=[VariableSnapshot(name=var, value=str(value), type="int")],
            )
        )
        index += 1
        printed = None
        if stdout and output_index < len(stdout):
            printed = stdout[output_index]
            output_index += 1
        else:
            printed = str(value)
        steps.append(
            ExecutionStep(
                index=index,
                label=f"STEP {index}",
                description=f"print {printed}",
                line=body_line,
                output_line=printed,
                variables=[VariableSnapshot(name=var, value=str(value), type="int")],
            )
        )
        index += 1
    steps.append(
        ExecutionStep(
            index=index,
            label=f"STEP {index}",
            description="range is exhausted — loop stops",
            line=max(1, body_line - 1),
            stopped=True,
            condition_result=False,
            variables=[VariableSnapshot(name=var, value=str(values[-1]), type="int")],
        )
    )
    return steps


def _steps_from_stdout(code: str, stdout: list[str]) -> list[ExecutionStep]:
    line = _print_line(code, fallback=1)
    steps: list[ExecutionStep] = []
    for index, printed in enumerate(stdout[:32], start=1):
        steps.append(
            ExecutionStep(
                index=index,
                label=f"STEP {index}",
                description=f"output: {printed}",
                line=line,
                output_line=printed,
                variables=[VariableSnapshot(name="out", value=printed, type="str")],
            )
        )
    return steps


def visualize_execution(language: str, code: str, stdout: list[str] | None = None) -> list[ExecutionStep]:
    lang = normalize_language(language)
    stdout = stdout or []
    if lang in {"java", "javascript"}:
        steps = _visualize_c_style(code, stdout)
        if steps:
            return steps
    if lang == "python":
        steps = _visualize_python_range(code, stdout)
        if steps:
            return steps
        steps = _visualize_c_style(code, stdout)
        if steps:
            return steps
    if stdout:
        return _steps_from_stdout(code, stdout)
    return []


def extract_primary_code(lesson_json: dict[str, Any]) -> tuple[str, str]:
    for scene in lesson_json.get("scenes", []):
        if scene.get("type") == "code" and scene.get("code"):
            return str(scene.get("language") or "java"), str(scene["code"])
        if scene.get("type") == "execution" and scene.get("code"):
            return str(scene.get("language") or "java"), str(scene["code"])
    return "java", ""
