#!/usr/bin/env python3
"""Polish: include reel_mode in planner message; localize diagram step text."""
from pathlib import Path

ROOT = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder")
orch = ROOT / "backend/app/agents/orchestrator.py"
ot = orch.read_text(encoding="utf-8")

ot = ot.replace(
    '        f"requires_code={plan.requires_code}\\n"\n'
    "    )\n"
    "    plan_mode = (getattr(plan, \"reel_mode\", None) or \"\").strip().lower()\n",
    '        f"requires_code={plan.requires_code}\\n"\n'
    '        f"reel_mode={getattr(plan, \'reel_mode\', None)}\\n"\n'
    "    )\n"
    "    plan_mode = (getattr(plan, \"reel_mode\", None) or \"\").strip().lower()\n",
    1,
)

# gather_teaching_texts: include diagram step titles/details
old_g = '''        texts.extend(list(getattr(scene, "bullets", None) or []))
        texts.extend(list(getattr(scene, "takeaways", None) or []))'''
new_g = '''        texts.extend(list(getattr(scene, "bullets", None) or []))
        for step in list(getattr(scene, "diagram_steps", None) or []):
            title = getattr(step, "title", None) or (step.get("title") if isinstance(step, dict) else None)
            detail = getattr(step, "detail", None) or (step.get("detail") if isinstance(step, dict) else None)
            if title:
                texts.append(str(title))
            if detail:
                texts.append(str(detail))
        texts.extend(list(getattr(scene, "takeaways", None) or []))'''
if old_g not in ot:
    raise SystemExit("gather_teaching_texts bullets block missing")
ot = ot.replace(old_g, new_g, 1)

orch.write_text(ot, encoding="utf-8")
print("polish ok")
