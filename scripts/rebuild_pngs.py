import hashlib
import json
import sqlite3
import subprocess
from pathlib import Path

ROOT = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder")
images = ROOT / "storage/images"
alt = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/storage/images")

for svg in images.glob("thumb_les_*.svg"):
    body = svg.read_text(encoding="utf-8")
    if "Roots" not in body and "INTERNALS" not in body and "HOW IT WORKS" not in body:
        # only rebuild current lesson svgs that are v8; still rebuild all with EXPLAINER badge
        if "EXPLAINER" not in body and "INFO REEL" not in body:
            continue
    png = svg.with_suffix(".png")
    subprocess.run(
        ["magick", "-background", "none", str(svg), "-resize", "540x960", str(png)],
        check=True,
        capture_output=True,
    )
    if alt.exists():
        import shutil
        shutil.copy2(svg, alt / svg.name)
        shutil.copy2(png, alt / png.name)
    print("built", png.name, png.stat().st_size)

con = sqlite3.connect(ROOT / "backend/tutor.db")
for lid, raw in con.execute("select id, lesson_json from lessons"):
    p = json.loads(raw)
    png = images / f"thumb_{lid}.png"
    if not png.exists():
        continue
    digest = hashlib.sha256(png.read_bytes()).hexdigest()[:10]
    url = f"/images/{png.name}?v=diagram-v8-hero-{digest}"
    p["thumbnail_url"] = url
    p["thumbnail_custom"] = False
    con.execute("update lessons set lesson_json=? where id=?", (json.dumps(p, ensure_ascii=False), lid))
    print("db", lid[:28], url)
con.commit()
con.close()

# previews
import shutil
prev = images / "previews"
prev.mkdir(exist_ok=True)
shutil.copy2(images / "thumb_les_34b2b09e272f43e389c24afcbfafc655.png", prev / "gc-v8.png")
shutil.copy2(images / "thumb_les_9aa6c519210a47a3b86e54fbf31419d3.png", prev / "hashmap-v8.png")
print("done")
