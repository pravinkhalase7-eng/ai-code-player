#!/usr/bin/env python3
import json
from pathlib import Path

path = Path("storage/tmp-lesson-peek.json")
if not path.exists():
    import urllib.request
    lid = "les_c212bc5cac73491c94c42d877b1950a4"
    with urllib.request.urlopen(f"http://127.0.0.1:8010/api/v1/lesson/{lid}", timeout=30) as r:
        path.write_bytes(r.read())

d = json.loads(path.read_text())
lesson = d.get("lesson") or d
print("title", lesson.get("title"))
print("mode", lesson.get("reel_mode"), "requires_code", lesson.get("requires_code"))
print("thumb", lesson.get("thumbnail_url"))
scenes = lesson.get("scenes") or []
print("scenes", len(scenes))
for s in scenes:
    vis = s.get("visual") or {}
    print("---", s.get("id"), "type", s.get("type"), "dur", s.get("duration"))
    print("  visual.kind", vis.get("kind"), "title", vis.get("title"), "callouts", vis.get("callouts"))
    print("  bullets", s.get("bullets"))
    print("  diagram_steps", s.get("diagram_steps"))
    print("  takeaways", s.get("takeaways"))
    segs = s.get("segments") or []
    print("  segments", len(segs))
    for x in segs[:5]:
        print("   ", x.get("start"), x.get("end"), (x.get("text") or "")[:80])
    print("  narr", (s.get("narration") or "")[:200])
