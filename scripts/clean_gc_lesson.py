import json, re, sqlite3
from pathlib import Path

# verify lesson_service syntax
import ast
ast.parse(Path("backend/app/services/lesson_service.py").read_text())
print("lesson_service.py syntax ok")

# simplify _strip function if broken - rewrite clean helpers
src = Path("backend/app/services/lesson_service.py").read_text()
# Replace overly complex strip with simple version
start = src.find("def _strip_appended_bullet_list")
end = src.find("def _spoken_scene_text")
if start < 0 or end < 0:
    raise SystemExit(f"markers missing {start} {end}")
simple = '''def _strip_appended_bullet_list(narration: str, bullets: list[str]) -> str:
    """Remove trailing on-screen bullet dumps that TTS enrichment used to persist."""
    text = (narration or "").strip()
    if not text:
        return text
    # Cut at first English numbered list dump like "1. Heap Allocation"
    m = re.search(r"([।.])\\s*1\\.\\s+[A-Za-z]", text)
    if m and m.start() > 40:
        return text[: m.start() + 1].strip()
    m = re.search(r"\\s1\\.\\s+[A-Za-z].*2\\.\\s+[A-Za-z]", text)
    if m and m.start() > 40:
        return text[: m.start()].rstrip(" .।") + ("।" if "।" in text[: m.start()] else ".")
    if bullets:
        first = bullets[0]
        idx = text.find(first)
        if idx > 40 and re.search(r"\\d+\\.\\s*" + re.escape(first), text[idx - 5 : idx + len(first) + 5]):
            prev = max(text.rfind("।", 0, idx), text.rfind(".", 0, idx))
            if prev > 20:
                return text[: prev + 1].strip()
    return text


'''
src = src[:start] + simple + src[end:]
Path("backend/app/services/lesson_service.py").write_text(src)
ast.parse(src)
print("strip helper simplified")

con = sqlite3.connect("backend/tutor.db")
lid = "les_3da70f1938974f21bec29ccf4e9833e6"
row = con.execute("select lesson_json from lessons where id=?", (lid,)).fetchone()
lesson = row[0] if isinstance(row[0], dict) else json.loads(row[0])
if isinstance(lesson, str):
    lesson = json.loads(lesson)
for scene in lesson.get("scenes") or []:
    if scene.get("type") != "concept":
        continue
    nar = scene.get("narration") or ""
    m = re.search(r"([।.])\s*1\.\s+Heap Allocation", nar)
    if m:
        nar = nar[: m.start() + 1].strip()
    else:
        idx = nar.find("1. Heap Allocation")
        if idx > 40:
            prev = max(nar.rfind("।", 0, idx), nar.rfind(".", 0, idx))
            nar = nar[: prev + 1].strip() if prev > 20 else nar[:idx].strip()
    # prefer segment join if cleaner
    segs = [str(s.get("text") or "").strip() for s in (scene.get("segments") or []) if str(s.get("text") or "").strip()]
    if segs and "Heap Allocation" not in " ".join(segs):
        nar = " ".join(segs)
    scene["narration"] = nar
    scene["audio_url"] = None
    print("FINAL", len(nar), "heap", nar.count("Heap"))
    print(nar)
con.execute("update lessons set lesson_json=? where id=?", (json.dumps(lesson, ensure_ascii=False), lid))
con.commit()
con.close()
print("db updated")
