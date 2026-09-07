#!/usr/bin/env python3
from pathlib import Path

ROOT = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder")
orch = ROOT / "backend/app/agents/orchestrator.py"
ot = orch.read_text(encoding="utf-8")

# Replace the messy block we just inserted
import re
pattern = r'''        steps = list\(getattr\(scene, "diagram_steps", None\) or \[\]\)
        if steps:
            from app\.schemas\.lesson import DiagramStep

            rebuilt = \[\]
            for step in steps:
                title = next\(cursor\)\[:120\]
                has_detail = bool\(
                    \(getattr\(step, "detail", None\) if not isinstance\(step, dict\) else step\.get\("detail"\)\) or ""
                \)
                detail = next\(cursor\)\[:240\] if has_detail else \(
                    getattr\(step, "detail", ""\) if not isinstance\(step, dict\) else str\(step\.get\("detail"\) or ""\)
                \)
                # gather always emits detail only when truthy — mirror that
                if has_detail:
                    rebuilt\.append\(DiagramStep\(title=title, detail=detail\)\)
                else:
                    # gather skipped empty detail; do not consume another line
                    rebuilt\.append\(DiagramStep\(title=title, detail=""\)\)
            updates\["diagram_steps"\] = rebuilt
'''

replacement = '''        steps = list(getattr(scene, "diagram_steps", None) or [])
        if steps:
            from app.schemas.lesson import DiagramStep

            rebuilt = []
            for step in steps:
                raw_title = getattr(step, "title", None) if not isinstance(step, dict) else step.get("title")
                raw_detail = getattr(step, "detail", None) if not isinstance(step, dict) else step.get("detail")
                title = next(cursor)[:120] if raw_title else str(raw_title or "")[:120]
                detail = next(cursor)[:240] if raw_detail else ""
                rebuilt.append(DiagramStep(title=title or "Step", detail=detail))
            updates["diagram_steps"] = rebuilt
'''

new_ot, n = re.subn(pattern, replacement, ot, count=1)
if n != 1:
    raise SystemExit(f"scatter diagram block replace failed n={n}")
orch.write_text(new_ot, encoding="utf-8")
print("scatter2 ok")
