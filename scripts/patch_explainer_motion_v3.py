#!/usr/bin/env python3
"""Prefer intro segments for cold-open; tighten orb styling for hook/takeaway."""
from pathlib import Path

ROOT = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder")
p = ROOT / "frontend/lib/explainerVisuals.ts"
t = p.read_text(encoding="utf-8")

old = '''  const takeaways = (scene.takeaways || []).map((t) => String(t || "").trim()).filter(Boolean);
  if (takeaways.length) {
    return takeaways.map((t) => ({ title: clip(t, 56), detail: "", example: "" }));
  }

  const callouts = (scene.visual?.callouts || []).map((c) => String(c || "").trim()).filter(Boolean);
  if (callouts.length) {
    return callouts.map((c) => ({ title: clip(c, 56), detail: "", example: "" }));
  }

  const segs = fromSegments(scene);
  if (segs.length >= 2) return segs;
'''

new = '''  const takeaways = (scene.takeaways || []).map((t) => String(t || "").trim()).filter(Boolean);
  if (takeaways.length) {
    return takeaways.map((t) => ({ title: clip(t, 56), detail: "", example: "" }));
  }

  // Intro cold-open: prefer real narration beats over truncated visual.callouts.
  const segs = fromSegments(scene);
  if (scene.type === "intro" && segs.length >= 1) return segs;

  const callouts = (scene.visual?.callouts || []).map((c) => String(c || "").trim()).filter(Boolean);
  if (callouts.length) {
    return callouts.map((c) => ({ title: clip(c, 56), detail: "", example: "" }));
  }

  if (segs.length >= 2) return segs;
'''

if old not in t:
    raise SystemExit("explainerVisuals block missing")
p.write_text(t.replace(old, new, 1), encoding="utf-8")
print("explainerVisuals intro preference ok")

# Also soft-improve intro callouts in DB to shorter hooks
import json, sqlite3
LID = "les_c212bc5cac73491c94c42d877b1950a4"
DB = ROOT / "backend/tutor.db"
con = sqlite3.connect(DB)
raw = con.execute("select lesson_json from lessons where id=?", (LID,)).fetchone()[0]
lesson = json.loads(raw)
for s in lesson.get("scenes") or []:
    if s.get("type") == "intro":
        s["visual"] = {
            "kind": "hook",
            "title": "Hook · Why learn Python?",
            "callouts": [
                "Python = confusing syntax?",
                "Nope — it reads like English",
                "Watch why pros pick it",
            ],
            "particles": True,
        }
        print("intro callouts tightened")
    if s.get("type") == "summary":
        # keep takeaways as callouts
        pass
con.execute("update lessons set lesson_json=? where id=?", (json.dumps(lesson, ensure_ascii=False), LID))
con.commit()
con.close()
print("db intro hooks updated")
