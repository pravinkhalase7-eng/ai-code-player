from __future__ import annotations

import logging
import re

from pydantic import BaseModel, Field

from app.errors import AppError
from app.services.gemini_client import structured_generate
from app.services.visualizer import normalize_language, source_filename

logger = logging.getLogger(__name__)

JAVA_LINE = re.compile(r"(?:[\w./]+)?Main\.java:(\d+)")
JAVA_LINE_ALT = re.compile(r"\.java:(\d+)")
PY_LINE = re.compile(r'File "[^"]+", line (\d+)')
PY_LINE_ALT = re.compile(r"line (\d+)")
JS_LINE = re.compile(r"(?:[\w./]+)?main\.js:(\d+)")
JS_LINE_ALT = re.compile(r"\.js:(\d+)")


class RunHelp(BaseModel):
    issue: str = Field(min_length=1, max_length=160)
    explanation: str = Field(min_length=1, max_length=1200)
    line: int | None = None
    label: str = Field(default="error", max_length=64)
    suggested_code: str | None = Field(default=None, max_length=20_000)


def parse_error_line(language: str, stderr: str) -> int | None:
    text = stderr or ""
    lang = normalize_language(language)
    patterns = {
        "java": (JAVA_LINE, JAVA_LINE_ALT),
        "python": (PY_LINE, PY_LINE_ALT),
        "javascript": (JS_LINE, JS_LINE_ALT, PY_LINE_ALT),
    }.get(lang, (JAVA_LINE, JAVA_LINE_ALT))
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            try:
                line = int(match.group(1))
            except (TypeError, ValueError):
                continue
            if line >= 1:
                return line
    return None


def _fallback_help(language: str, stderr: str, compile_error: bool, timed_out: bool) -> RunHelp:
    line = parse_error_line(language, stderr)
    if timed_out:
        return RunHelp(
            issue="time limit",
            explanation="This program never finished. Check the loop condition and make sure the counter actually changes.",
            line=line,
            label="loop",
        )
    if compile_error:
        return RunHelp(
            issue="compile error",
            explanation=(
                f"The compiler stopped on line {line}. Read that line first — a missing semicolon, brace, or name usually sits there."
                if line
                else "The compiler rejected this file. Read the first error in the terminal; it names the line to fix."
            ),
            line=line,
            label="compiler",
        )
    return RunHelp(
        issue="runtime error",
        explanation=(
            f"The program crashed on line {line}. That line ran, then failed — check the value being used there."
            if line
            else "The program started, then crashed. The terminal message is the real error; we will highlight it if a line number is present."
        ),
        line=line,
        label="crash",
    )


def explain_run_error(
    *,
    language: str,
    code: str,
    stderr: str,
    compile_error: bool,
    timed_out: bool,
    topic: str = "",
) -> RunHelp:
    fallback = _fallback_help(language, stderr, compile_error, timed_out)
    filename = source_filename(language)
    try:
        drafted = structured_generate(
            (
                "You are Byte, a visual coding tutor sitting next to the student.\n"
                "They clicked Run and it failed. Explain the REAL error in 2-4 short spoken sentences.\n"
                "Point at the exact line. If you can fix it confidently, return the full corrected source.\n"
                "Do not invent a different program. Keep the student's approach."
            ),
            (
                f"Language: {language}\n"
                f"Filename: {filename}\n"
                f"Lesson topic: {topic or 'this example'}\n"
                f"compile_error={compile_error} timed_out={timed_out}\n"
                f"Error output:\n{stderr[:2500]}\n\n"
                f"Student code:\n{code[:8000]}"
            ),
            RunHelp,
            temperature=0.15,
            label="run_help",
        )
    except AppError:
        logger.warning("run-help Gemini unavailable, using parsed compiler line")
        return fallback
    except Exception:
        logger.exception("run-help failed")
        return fallback

    line = drafted.line or fallback.line
    suggested = drafted.suggested_code.strip() if drafted.suggested_code else None
    if suggested and suggested == code.strip():
        suggested = None
    return drafted.model_copy(
        update={
            "line": line,
            "label": drafted.label or fallback.label,
            "suggested_code": suggested,
            "explanation": drafted.explanation or fallback.explanation,
        }
    )
