from pathlib import Path
import sqlite3, json, wave

ROOT = Path(__file__).resolve().parents[1]
LID = "les_21c34e4cfbbf47a8bc4d476d554fba51"
con = sqlite3.connect(ROOT / "backend" / "tutor.db")
row = con.execute(
    "select id, topic, status, lesson_json from lessons where id=?", (LID,)
).fetchone()
if not row:
    print("LESSON NOT FOUND")
    for r in con.execute(
        "select id, topic, status from lessons order by rowid desc limit 10"
    ):
        print(" ", r)
    raise SystemExit(0)

lid, topic, status, raw = row
p = json.loads(raw)
print("topic:", topic)
print("status:", status)
print(
    "reel_mode:",
    p.get("reel_mode"),
    "format:",
    p.get("format"),
    "reel_seconds:",
    p.get("reel_seconds"),
)
print("spoken:", p.get("spoken_language"), "lang:", p.get("language"))


def wav_duration(path: Path):
    try:
        with wave.open(str(path), "rb") as w:
            return w.getnframes() / float(w.getframerate())
    except Exception as e:
        return f"err:{e}"


for i, s in enumerate(p.get("scenes") or []):
    st = s.get("type")
    dur = s.get("duration")
    segs = s.get("segments") or []
    audio = s.get("audio_url") or ""
    narr = s.get("narration") or ""
    bullets = s.get("bullets") or []
    steps = s.get("diagram_steps") or []
    visual = s.get("visual_diagram")
    last_end = max((seg.get("end") or 0) for seg in segs) if segs else 0
    print(f"\n=== scene[{i}] {st} id={s.get('id')} ===")
    print(
        f"  duration={dur} segs={len(segs)} last_end={last_end} audio={audio}"
    )
    print(
        f"  narr_len={len(narr)} bullets={len(bullets)} diagram_steps={len(steps)} visual={bool(visual)}"
    )
    if narr:
        print("  narr:", narr[:220].replace("\n", " "))
    if steps:
        for j, d in enumerate(steps):
            print(
                f"  step{j+1}: {d.get('title')} | ex={(d.get('example') or '')[:60]}"
            )
    if segs:
        for j, seg in enumerate(segs[:16]):
            print(
                f"  seg{j}: {seg.get('start'):.2f}-{seg.get('end'):.2f} {(seg.get('text') or '')[:80]}"
            )
        if len(segs) > 16:
            print(f"  ... +{len(segs)-16} more")
    if audio:
        name = Path(audio).name
        found = None
        for base in [
            ROOT / "storage" / "audio",
            ROOT / "backend" / "storage" / "audio",
        ]:
            if not base.is_dir():
                continue
            direct = base / name
            if direct.is_file():
                found = direct
                break
            hits = list(base.rglob(name)) + list(base.rglob(f"*{lid}*"))
            if hits:
                found = hits[0]
                break
        if found:
            print(f"  audio_file={found} dur={wav_duration(found)}")
        else:
            print("  audio_file=NOT FOUND", name)

print("\nFULL concept scene keys sample done")
