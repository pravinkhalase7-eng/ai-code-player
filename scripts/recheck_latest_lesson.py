from pathlib import Path
import sqlite3, json, wave, re

ROOT = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder")
con = sqlite3.connect(ROOT / "backend/tutor.db")
rows = con.execute(
    "select id, topic, status, lesson_json, updated_at from lessons order by rowid desc limit 5"
).fetchall()
print("=== recent lessons ===")
for r in rows:
    print(r[0], r[2], (r[1] or "")[:60], "upd", r[4])

if not rows:
    print("NO LESSONS")
    raise SystemExit(0)

lid, topic, status, raw, _ = rows[0]
p = json.loads(raw)
print("\n=== FOCUS", lid, "===")
print("topic:", topic)
print("status:", status)
print("format:", p.get("format"), "reel_mode:", p.get("reel_mode"), "reel_seconds:", p.get("reel_seconds"))
print("spoken:", p.get("spoken_language"), "thumb:", p.get("thumbnail_url"))
print("custom_thumb:", p.get("thumbnail_custom"))

# thumbnail file
thumb_url = p.get("thumbnail_url") or ""
name = Path(thumb_url.split("?")[0]).name if thumb_url else ""
thumb_path = ROOT / "storage/images" / name
print("thumb_file:", thumb_path, "exists", thumb_path.is_file())
if thumb_path.is_file():
    body = thumb_path.read_text(encoding="utf-8", errors="ignore")
    print("  has concept only:", "concept only" in body)
    print("  has HASHMAP:", "HASHMAP" in body)
    print("  has GC:", "GC · HEAP" in body or "GC" in body)
    print("  has HOW IT WORKS:", "HOW IT WORKS" in body)
    print("  has EXPLAINER:", "EXPLAINER" in body)
    print("  version query:", thumb_url)
    # check if diagram group present
    print("  bytes", thumb_path.stat().st_size)

def wav_dur(path):
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / float(w.getframerate())

issues = []
for i, s in enumerate(p.get("scenes") or []):
    st = s.get("type")
    dur = float(s.get("duration") or 0)
    segs = s.get("segments") or []
    last = max((float(seg.get("end") or 0) for seg in segs), default=0)
    audio = s.get("audio_url") or ""
    steps = s.get("diagram_steps") or []
    visual = s.get("visual_diagram")
    narr = s.get("narration") or ""
    audio_path = ROOT / "storage/audio" / Path(audio).name if audio else None
    ad = None
    if audio_path and audio_path.is_file():
        ad = wav_dur(audio_path)
    print(f"\nscene[{i}] {st}")
    print(f"  duration={dur} last_seg={last} audio_wav={ad} steps={len(steps)} segs={len(segs)} visual={bool(visual)}")
    print(f"  narr_len={len(narr)} audio_url={audio}")
    if ad and abs(dur - ad) > 0.8:
        issues.append(f"{st}: duration {dur} vs wav {ad:.2f}")
    if ad and last and abs(last - ad) > 0.8:
        issues.append(f"{st}: last_seg {last} vs wav {ad:.2f}")
    if not audio:
        issues.append(f"{st}: missing audio_url")
    if st == "concept" and p.get("reel_mode") == "explainer":
        if not steps:
            issues.append("concept: no diagram_steps")
        if re.search(r"hash\s*map", (topic or "").lower()) and not visual:
            issues.append("hashmap concept: missing visual_diagram")
        if steps and segs and abs(len(steps) - len(segs)) >= 1:
            issues.append(f"concept: {len(steps)} steps vs {len(segs)} segments (board uses equal-split fallback)")
    if "1. " in narr and re.search(r"\n?\s*1\.\s+[A-Za-z].*2\.\s+", narr):
        issues.append(f"{st}: narration may contain appended bullet dump")

print("\n=== ISSUES ===")
if not issues:
    print("none detected in data")
else:
    for x in issues:
        print("-", x)

# code presence of fixes
checks = {
    "beats rescale": "Math.abs(dur - last.end) > 0.45" in (ROOT/"frontend/lib/infoReelAnim.ts").read_text(),
    "step/seg equal-split": "diagramSteps.length - segs.length" in (ROOT/"frontend/components/player/ReelStage.tsx").read_text(),
    "align after TTS": "_align_scene_to_audio" in (ROOT/"backend/app/services/lesson_service.py").read_text(),
    "diagram thumbs": "diagram-v7-explainer" in (ROOT/"backend/app/services/images/thumbnail.py").read_text(),
    "MechanismBoard wired": "MechanismBoard" in (ROOT/"frontend/components/player/ReelStage.tsx").read_text(),
}
print("\n=== FIXES PRESENT ===")
for k,v in checks.items():
    print(("OK" if v else "MISSING"), k)
