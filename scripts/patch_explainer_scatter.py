#!/usr/bin/env python3
from pathlib import Path

ROOT = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder")
orch = ROOT / "backend/app/agents/orchestrator.py"
ot = orch.read_text(encoding="utf-8")

old = '''        bullets = getattr(scene, "bullets", None)
        if bullets:
            updates["bullets"] = [next(cursor) for _ in bullets]
        takeaways = getattr(scene, "takeaways", None)'''

new = '''        bullets = getattr(scene, "bullets", None)
        if bullets:
            updates["bullets"] = [next(cursor) for _ in bullets]
        steps = list(getattr(scene, "diagram_steps", None) or [])
        if steps:
            from app.schemas.lesson import DiagramStep

            rebuilt = []
            for step in steps:
                title = next(cursor)[:120]
                has_detail = bool(
                    (getattr(step, "detail", None) if not isinstance(step, dict) else step.get("detail")) or ""
                )
                detail = next(cursor)[:240] if has_detail else (
                    getattr(step, "detail", "") if not isinstance(step, dict) else str(step.get("detail") or "")
                )
                # gather always emits detail only when truthy — mirror that
                if has_detail:
                    rebuilt.append(DiagramStep(title=title, detail=detail))
                else:
                    # gather skipped empty detail; do not consume another line
                    rebuilt.append(DiagramStep(title=title, detail=""))
            updates["diagram_steps"] = rebuilt
        takeaways = getattr(scene, "takeaways", None)'''

if old not in ot:
    raise SystemExit("scatter bullets block missing")
ot = ot.replace(old, new, 1)
orch.write_text(ot, encoding="utf-8")
print("scatter patched — verifying gather/scatter pairing logic next")
