from pathlib import Path
import json, re, sqlite3, sys

# --- 1) Fix lesson_service.py ---
path = Path("backend/app/services/lesson_service.py")
text = path.read_text()

old_spoken = '''def _spoken_scene_text(lesson: Lesson, scene: Any) -> str:
    narration = teachable_narration(scene.narration, lesson.spoken_language, scene.narration)
    if getattr(scene, "type", "") == "intro":
        return hook_narration(narration, lesson.spoken_language, lesson.topic, lesson.lesson_id)
    if getattr(scene, "type", "") == "concept":
        bullets = [str(b).strip() for b in (getattr(scene, "bullets", None) or []) if str(b).strip()]
        if bullets:
            joined = ". ".join(bullets)
            if narration and narration.strip() and narration.strip() not in joined:
                return f"{narration.strip()}. {joined}"
            return joined
    return narration
'''

new_spoken = '''def _strip_appended_bullet_list(narration: str, bullets: list[str]) -> str:
    """Remove trailing on-screen bullet dumps that TTS enrichment used to persist."""
    text = (narration or "").strip()
    if not text or not bullets:
        return text
    # Drop one or more trailing copies of "1. A. 2. B. ..." style lists.
    joined = ". ".join(b.strip() for b in bullets if b.strip())
    if not joined:
        return text
    pattern = re.compile(
        r"(?:\\.\\s*)?(?:\\d+\\.\\s*)?" + re.escape(bullets[0].strip()) + r".*$",
        re.IGNORECASE | re.DOTALL,
    )
    # Prefer chopping at first occurrence of the first bullet title after sentence end.
    idx = text.find(bullets[0].strip())
    if idx > 40:
        # walk back to previous danda/period
        cut = text.rfind("।", 0, idx)
        if cut < 0:
            cut = text.rfind(".", 0, idx)
        if cut > 20:
            text = text[: cut + 1].strip()
    # Also collapse if joined list repeats
    while joined in text and text.count(joined) > 0 and text.strip().endswith(joined.split(".")[-1].strip()) is False:
        # remove trailing repeated joined blocks
        if text.endswith(joined):
            text = text[: -len(joined)].rstrip(" .।")
        elif f". {joined}" in text:
            text = text.split(f". {joined}")[0].strip()
            break
        else:
            break
    # Generic: if "1. " appears and looks like a numbered list dump, cut from first "1. "
    m = re.search(r"[।.]\\s*1\\.\\s+\\S+", text)
    if m and m.start() > 40:
        text = text[: m.start() + 1].strip()
    return text


def _spoken_scene_text(lesson: Lesson, scene: Any) -> str:
    bullets = [str(b).strip() for b in (getattr(scene, "bullets", None) or []) if str(b).strip()]
    cleaned = _strip_appended_bullet_list(scene.narration or "", bullets)
    narration = teachable_narration(cleaned, lesson.spoken_language, cleaned)
    if getattr(scene, "type", "") == "intro":
        return hook_narration(narration, lesson.spoken_language, lesson.topic, lesson.lesson_id)
    # Concept/explainer: on-screen bullets/diagram titles stay visual-only.
    # Never append them into TTS — that used to persist and multiply on each audio refresh.
    return narration
'''

if old_spoken not in text:
    # try already patched
    if "Never append them into TTS" in text:
        print("spoken already patched")
    else:
        raise SystemExit("spoken block not found")
else:
    text = text.replace(old_spoken, new_spoken, 1)
    print("patched _spoken_scene_text")

# ensure `import re` exists
if "\nimport re\n" not in text and not text.startswith("import re"):
    text = text.replace("\nimport ", "\nimport re\nimport ", 1)
    print("added import re")

old_assets = '''        narration = _spoken_scene_text(lesson, scene)
        scene_patch: dict[str, Any] = {}
        if narration != scene.narration:
            scene_patch["narration"] = narration
            scene_patch["audio_url"] = None
        audio_url = scene.audio_url if not scene_patch else None
        if narration.strip():
'''

new_assets = '''        # Sanitize persisted narration if an older TTS pass appended bullet lists.
        bullets = [str(b).strip() for b in (getattr(scene, "bullets", None) or []) if str(b).strip()]
        cleaned_narration = _strip_appended_bullet_list(scene.narration or "", bullets)
        scene_patch: dict[str, Any] = {}
        if cleaned_narration != (scene.narration or "").strip():
            scene_patch["narration"] = cleaned_narration
            scene = scene.model_copy(update={"narration": cleaned_narration})
            scene_patch["audio_url"] = None
        spoken = _spoken_scene_text(lesson, scene)
        # Speak `spoken` but do NOT write TTS enrichment back into narration.
        audio_url = None if "audio_url" in scene_patch else scene.audio_url
        if spoken.strip():
'''

if old_assets not in text:
    if "do NOT write TTS enrichment" in text:
        print("assets already patched")
    else:
        raise SystemExit("assets block not found")
else:
    text = text.replace(old_assets, new_assets, 1)
    # fix synthesize call to use spoken
    text = text.replace(
        "audio_url, used = synthesize_narration(\n                    db, narration, provider_name=\"google\", voice=voice\n                )",
        "audio_url, used = synthesize_narration(\n                    db, spoken, provider_name=\"google\", voice=voice\n                )",
        1,
    )
    print("patched generate_lesson_assets")

path.write_text(text)

# --- 2) Fix this lesson in DB ---
con = sqlite3.connect("backend/tutor.db")
row = con.execute("select lesson_json from lessons where id=?", ("les_3da70f1938974f21bec29ccf4e9833e6",)).fetchone()
lesson = row[0] if isinstance(row[0], dict) else json.loads(row[0])
if isinstance(lesson, str):
    lesson = json.loads(lesson)
for scene in lesson.get("scenes") or []:
    if scene.get("type") != "concept":
        continue
    bullets = [str(b).strip() for b in (scene.get("bullets") or []) if str(b).strip()]
    nar = scene.get("narration") or ""
    # cut at English list
    m = re.search(r"[।.]\\s*1\\.\\s+Heap Allocation", nar)
    if not m:
        m = re.search(r"1\\.\\s+Heap Allocation", nar)
    if m and m.start() > 20:
        # include the danda/period before list
        cut = m.start() + (1 if nar[m.start()] in "।." else 0)
        if nar[m.start()] in "।.":
            nar = nar[: m.start() + 1].strip()
        else:
            # find prior sentence end
            prev = max(nar.rfind("।", 0, m.start()), nar.rfind(".", 0, m.start()))
            nar = nar[: prev + 1].strip() if prev > 20 else nar[: m.start()].strip()
    scene["narration"] = nar
    scene["audio_url"] = None  # force regen without bullet dump
    print("cleaned narration len", len(nar))
    print(nar[:220])
con.execute("update lessons set lesson_json=? where id=?", (json.dumps(lesson, ensure_ascii=False), "les_3da70f1938974f21bec29ccf4e9833e6"))
con.commit()
sys.path.insert(0, "backend")
from app.schemas.lesson import Lesson
from app.services.lesson_service import _spoken_scene_text, _strip_appended_bullet_list
Lesson.model_validate(lesson)
concept = next(s for s in Lesson.model_validate(lesson).scenes if s.type == "concept")
spoken = _spoken_scene_text(Lesson.model_validate(lesson), concept)
print("spoken has Heap?", "Heap Allocation" in spoken)
print("spoken len", len(spoken))
con.close()
print("done")
