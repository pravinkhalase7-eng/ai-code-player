#!/usr/bin/env python3
"""Fill visual payloads on les_c212… and force-regen thumbnail."""
import json
import sqlite3
import sys
import urllib.request
from pathlib import Path

ROOT = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder")
LID = "les_c212bc5cac73491c94c42d877b1950a4"
DB = ROOT / "backend/tutor.db"

sys.path.insert(0, str(ROOT / "backend"))

con = sqlite3.connect(DB)
row = con.execute("select id, lesson_json from lessons where id=?", (LID,)).fetchone()
if not row:
    # try lesson_id inside json
    for rid, raw in con.execute("select id, lesson_json from lessons").fetchall():
        p = json.loads(raw)
        if p.get("lesson_id") == LID or rid == LID:
            row = (rid, raw)
            break
if not row:
    raise SystemExit(f"lesson {LID} not in db")

rid, raw = row
lesson = json.loads(raw)
print("db id", rid, "title", lesson.get("title"), "mode", lesson.get("reel_mode"))

# Import synth from orchestrator
from app.agents.orchestrator import _synth_visual_for_scene
from app.schemas.lesson import Lesson

validated = Lesson.model_validate(lesson)
updated_scenes = []
for scene in validated.scenes:
    patch = _synth_visual_for_scene(scene, validated)
    if patch:
        scene = scene.model_copy(update=patch)
    vis = scene.visual
    print(f"  {scene.type}: kind={vis.kind} callouts={len(vis.callouts)} title={vis.title[:40]!r}")
    updated_scenes.append(scene)

updated = validated.model_copy(update={"scenes": updated_scenes})
payload = updated.model_dump(mode="json")
# keep any extra fields
for k, v in lesson.items():
    if k not in payload:
        payload[k] = v

con.execute(
    "update lessons set lesson_json=? where id=?",
    (json.dumps(payload, ensure_ascii=False), rid),
)
con.commit()
con.close()
print("lesson visuals patched in db")

# Force thumb regen via API
url = f"http://127.0.0.1:8010/api/v1/lesson/{LID}/thumbnail?force=true"
req = urllib.request.Request(url, method="POST", data=b"")
try:
    with urllib.request.urlopen(req, timeout=120) as resp:
        d = json.load(resp)
    les = d.get("lesson") or d
    print("thumb_url", les.get("thumbnail_url"))
except Exception as e:
    print("API thumb regen failed (will retry after restart):", e)
    # Direct ensure
    from app.services.images.thumbnail import ensure_reel_thumbnail, THUMB_VERSION
    print("THUMB_VERSION", THUMB_VERSION)
    url2 = ensure_reel_thumbnail(
        LID,
        lesson.get("topic") or "",
        lesson.get("title") or lesson.get("topic") or "",
        lesson.get("language") or "python",
        None,
        reel_mode=lesson.get("reel_mode"),
        spoken_language=lesson.get("spoken_language"),
    )
    print("direct thumb", url2)
    # write back
    con = sqlite3.connect(DB)
    raw = con.execute("select lesson_json from lessons where id=?", (rid,)).fetchone()[0]
    p = json.loads(raw)
    p["thumbnail_url"] = url2
    p["thumbnail_custom"] = False
    con.execute("update lessons set lesson_json=? where id=?", (json.dumps(p, ensure_ascii=False), rid))
    con.commit()
    con.close()
