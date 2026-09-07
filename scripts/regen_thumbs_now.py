import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder")
sys.path.insert(0, str(ROOT / "backend"))
from importlib import reload
import app.services.images.thumbnail as th
reload(th)

con = sqlite3.connect(ROOT / "backend/tutor.db")
for lid, raw in con.execute("select id, lesson_json from lessons").fetchall():
    p = json.loads(raw)
    if p.get("format") != "reel":
        continue
    url = th.ensure_reel_thumbnail(
        p.get("lesson_id") or lid,
        p.get("topic") or "",
        p.get("topic") or p.get("title") or "",
        p.get("language") or "java",
        None,
        reel_mode=p.get("reel_mode"),
    )
    p["thumbnail_url"] = url
    p["thumbnail_custom"] = False
    con.execute(
        "update lessons set lesson_json=? where id=?",
        (json.dumps(p, ensure_ascii=False), lid),
    )
    svg = ROOT / "storage/images" / f"thumb_{lid}.svg"
    body = svg.read_text(encoding="utf-8") if svg.exists() else ""
    print(lid[:28], url)
    print("  markers:", [m for m in ["Roots", "MARK &amp; SWEEP", "INTERNALS", "GC · HEAP", "BUCKETS", "concept only"] if m in body])
con.commit()
con.close()

# copy previews
import shutil
preview = ROOT / "storage/images/previews"
preview.mkdir(exist_ok=True)
for src, dst in [
    ("thumb_les_34b2b09e272f43e389c24afcbfafc655.png", "gc-v8.png"),
    ("thumb_les_9aa6c519210a47a3b86e54fbf31419d3.png", "hashmap-v8.png"),
]:
    s = ROOT / "storage/images" / src
    if s.exists():
        shutil.copy(s, preview / dst)
        print("preview", dst, s.stat().st_size)
