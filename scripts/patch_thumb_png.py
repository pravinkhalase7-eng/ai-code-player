from pathlib import Path
import json
import sqlite3
import subprocess
import sys
import hashlib

ROOT = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder")
thumb = ROOT / "backend/app/services/images/thumbnail.py"
text = thumb.read_text()

old = '''    write_svg_poster(
        svg_path, topic, poster_title, language, code, reel_mode=reel_mode
    )
    # Content hash so browsers cannot keep an old SVG under the same filename.
    digest = hashlib.sha256(svg_path.read_bytes()).hexdigest()[:10]
    return f"/images/{svg_path.name}?v={THUMB_VERSION}-{digest}"
'''
new = '''    write_svg_poster(
        svg_path, topic, poster_title, language, code, reel_mode=reel_mode
    )
    # Prefer PNG for dashboard/img tags — avoids stubborn SVG caching and sharper cards.
    png_path = svg_path.with_suffix(".png")
    try:
        import subprocess as _sp
        _sp.run(
            [
                "magick",
                "-background",
                "none",
                str(svg_path),
                "-resize",
                "540x960",
                str(png_path),
            ],
            check=True,
            capture_output=True,
        )
        digest = hashlib.sha256(png_path.read_bytes()).hexdigest()[:10]
        return f"/images/{png_path.name}?v={THUMB_VERSION}-{digest}"
    except Exception:
        digest = hashlib.sha256(svg_path.read_bytes()).hexdigest()[:10]
        return f"/images/{svg_path.name}?v={THUMB_VERSION}-{digest}"
'''
if old not in text:
    raise SystemExit("ensure return block not found")
thumb.write_text(text.replace(old, new, 1))
print("ensure now emits png when magick works")

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
    con.execute("update lessons set lesson_json=? where id=?", (json.dumps(p, ensure_ascii=False), lid))
    print("url", lid[:24], url)
con.commit()
con.close()

# Dashboard: bust cache by appending nothing if already has ?v=; also reload list on visibility
dash = ROOT / "frontend/components/dashboard/Dashboard.tsx"
dt = dash.read_text()
if "document.visibilityState" not in dt:
    old_fx = '''  useEffect(() => {
    setSpokenLanguage(readStoredSpokenLanguage());
    setFormat(readStoredFormat());
    setReelSeconds(readStoredReelSeconds());
    void listLessons()
      .then((payload) => setLessons(payload.lessons))
      .catch(() => undefined);
    void getHealth()
'''
    new_fx = '''  useEffect(() => {
    setSpokenLanguage(readStoredSpokenLanguage());
    setFormat(readStoredFormat());
    setReelSeconds(readStoredReelSeconds());
    const loadLessons = () =>
      void listLessons()
        .then((payload) => setLessons(payload.lessons))
        .catch(() => undefined);
    loadLessons();
    const onVis = () => {
      if (document.visibilityState === "visible") loadLessons();
    };
    document.addEventListener("visibilitychange", onVis);
    void getHealth()
'''
    if old_fx not in dt:
        print("dashboard effect not patched - pattern missing")
    else:
        dt = dt.replace(old_fx, new_fx, 1)
        # close the effect with removeEventListener - find the end of this useEffect
        old_end = '''      .catch(() => setHealth("Backend offline"));
  }, []);
'''
        new_end = '''      .catch(() => setHealth("Backend offline"));
    return () => document.removeEventListener("visibilitychange", onVis);
  }, []);
'''
        if old_end not in dt:
            print("dashboard effect end missing")
        else:
            dt = dt.replace(old_end, new_end, 1)
            dash.write_text(dt)
            print("dashboard refreshes lessons on tab focus")
else:
    print("dashboard already refreshes")

# preview png for user
gc = ROOT / "storage/images/thumb_les_34b2b09e272f43e389c24afcbfafc655.png"
hm = ROOT / "storage/images/thumb_les_9aa6c519210a47a3b86e54fbf31419d3.png"
preview = ROOT / "storage/images/previews"
preview.mkdir(exist_ok=True)
import shutil
shutil.copy(gc, preview / "gc-v8.png")
shutil.copy(hm, preview / "hashmap-v8.png")
print("preview", gc.exists(), gc.stat().st_size if gc.exists() else 0)
