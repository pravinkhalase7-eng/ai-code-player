import json, re, sqlite3, wave
from pathlib import Path

con = sqlite3.connect("backend/tutor.db")
rows = con.execute(
    "select id, topic, status, lesson_json from lessons order by updated_at desc limit 25"
).fetchall()

bullet_dump = re.compile(r"1\.\s+\S+.*2\.\s+\S+", re.S)
issues = []

for lid, topic, status, raw in rows:
    lesson = raw if isinstance(raw, dict) else json.loads(raw)
    if isinstance(lesson, str):
        lesson = json.loads(lesson)
    fmt = lesson.get("format")
    mode = lesson.get("reel_mode")
    req = lesson.get("requires_code")
    if fmt != "reel":
        continue
    entry = {
        "id": lid,
        "topic": topic,
        "status": status,
        "reel_mode": mode,
        "requires_code": req,
        "problems": [],
    }
    for scene in lesson.get("scenes") or []:
        st = scene.get("type")
        nar = scene.get("narration") or ""
        segs = scene.get("segments") or []
        audio = scene.get("audio_url") or ""
        dur = float(scene.get("duration") or 0)
        last_seg = max((float(s.get("end") or 0) for s in segs), default=0)
        # narration bullet dump
        if bullet_dump.search(nar) and nar.count("1.") >= 2:
            entry["problems"].append(f"{st}: narration has numbered list dump (len={len(nar)}, repeats?)")
        if nar.count("Heap Allocation") > 1 or nar.count("1. ") > 6:
            entry["problems"].append(f"{st}: repeated english steps in narration")
        if len(nar) > 1800:
            entry["problems"].append(f"{st}: narration very long ({len(nar)})")
        # segment vs duration mismatch
        if segs and last_seg > dur + 5:
            entry["problems"].append(f"{st}: segments end {last_seg:.1f}s > scene.duration {dur:.1f}s")
        # audio duration vs cues
        if audio.startswith("/audio/"):
            wav = Path("storage") / audio.lstrip("/")
            if wav.exists():
                try:
                    with wave.open(str(wav), "rb") as w:
                        adur = w.getnframes() / float(w.getframerate())
                    if segs and adur > last_seg + 15:
                        entry["problems"].append(
                            f"{st}: audio {adur:.1f}s >> last cue {last_seg:.1f}s (silent padding)"
                        )
                    if dur > 0.5 and adur > dur * 3 and adur > 40:
                        entry["problems"].append(
                            f"{st}: audio {adur:.1f}s vs duration {dur:.1f}s"
                        )
                except Exception as e:
                    entry["problems"].append(f"{st}: wav read fail {e}")
            else:
                entry["problems"].append(f"{st}: missing audio file {audio}")
        elif mode in ("explainer", "info") or req is False:
            if st in ("intro", "concept", "summary") and not audio:
                entry["problems"].append(f"{st}: missing audio_url")
        # explainer hashmap without visual
        if mode == "explainer" and st == "concept":
            vd = scene.get("visual_diagram") or {}
            steps = scene.get("diagram_steps") or []
            if not steps and not vd:
                entry["problems"].append("concept: no diagram_steps and no visual_diagram")
            topic_l = (topic or "").lower()
            if ("hashmap" in topic_l or "hash map" in topic_l) and vd.get("kind") != "hashmap":
                entry["problems"].append("hashmap topic but visual_diagram.kind != hashmap")
    if entry["problems"]:
        issues.append(entry)

print(f"checked {sum(1 for r in rows if True)} lessons (latest 25), reel issues:")
if not issues:
    print("NONE FOUND in latest reel lessons")
for e in issues:
    print("---", e["id"], "|", e["topic"], "| mode=", e["reel_mode"])
    for p in e["problems"]:
        print(" ", p)

# also scan code for remaining append bullets to narration
svc = Path("backend/app/services/lesson_service.py").read_text()
print("\nCODE:")
print(" never-append marker", "Never append them into TTS" in svc)
print(" still joins bullets?", 'return f"{narration.strip()}. {joined}"' in svc)
