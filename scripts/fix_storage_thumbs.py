import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder")
sys.path.insert(0, str(ROOT / "backend"))

# Import with backend as cwd semantics
import os
os.chdir(ROOT / "backend")

from importlib import reload
import app.services.images.thumbnail as th
from app.config import settings
reload(th)

print("storage_path setting:", settings.storage_path)
print("resolved:", Path(settings.storage_path).resolve())
images = Path(settings.storage_path).resolve() / "images"
images.mkdir(parents=True, exist_ok=True)
print("images dir:", images)

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
    svg = images / f"thumb_{lid}.svg"
    body = svg.read_text(encoding="utf-8") if svg.exists() else ""
    print(lid[:28], url)
    print("  path", svg)
    print("  markers", [m for m in ["Roots", "INTERNALS", "MARK &amp; SWEEP", "GC · HEAP", "BUCKETS", "concept only"] if m in body])
con.commit()
con.close()

# also copy into ai-coder/storage for convenience
import shutil
dest = ROOT / "storage/images"
dest.mkdir(parents=True, exist_ok=True)
for f in images.glob("thumb_les_*.svg"):
    shutil.copy2(f, dest / f.name)
for f in images.glob("thumb_les_*.png"):
    shutil.copy2(f, dest / f.name)
print("synced copies into ai-coder/storage/images")

# previews from resolved path
preview = ROOT / "storage/images/previews"
preview.mkdir(exist_ok=True)
for name, out in [
    ("thumb_les_34b2b09e272f43e389c24afcbfafc655.png", "gc-v8.png"),
    ("thumb_les_9aa6c519210a47a3b86e54fbf31419d3.png", "hashmap-v8.png"),
]:
    src = images / name
    if src.exists():
        shutil.copy2(src, preview / out)
        print("preview", out, src.stat().st_size)
