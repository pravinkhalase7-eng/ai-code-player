#!/usr/bin/env python3
"""Jenkins / CI smoke test for the AI Coding Tutor API image."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite:///./jenkins_smoke.db")
os.environ.setdefault("GEMINI_API_KEY", "")
os.environ.setdefault("TTS_PROVIDER", "browser")
os.environ.setdefault("TTS_FALLBACK_PROVIDER", "browser")
os.environ.setdefault("GOOGLE_TTS_API_KEY", "")
os.environ.setdefault("CODE_RUNNER_URL", "http://127.0.0.1:8090")
os.environ.setdefault("STORAGE_PATH", "/tmp/ai-coder-smoke")

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def main() -> int:
    from app.main import app
    from app.services.run_help import parse_error_line
    from app.services.visualizer import visualize_execution

    assert app.title, "app title missing"
    print("import_ok", app.title)

    steps = visualize_execution("python", "for i in range(3):\n    print(i)\n", ["0", "1", "2"])
    printed = [step.output_line for step in steps if step.output_line]
    if printed != ["0", "1", "2"]:
        print("FAIL visualizer", printed, file=sys.stderr)
        return 1
    print("visualizer_ok", len(steps))

    line = parse_error_line("java", "Main.java:5: error: ';' expected")
    if line != 5:
        print("FAIL parse_error_line", line, file=sys.stderr)
        return 1
    print("run_help_ok", line)
    print("smoke_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
