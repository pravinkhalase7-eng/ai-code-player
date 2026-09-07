import sqlite3
from pathlib import Path

root = Path(__file__).resolve().parents[1]
db = root / "backend" / "tutor.db"
audio_dir = root / "storage" / "audio"

con = sqlite3.connect(db)
tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
print("tables:", tables)
for t in tables:
    n = con.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
    print(f"  before {t}: {n}")

# Prefer deleting known lesson tables; also wipe related rows if present
deleted = {}
for t in tables:
    low = t.lower()
    if low in {"lessons", "lesson", "lesson_assets", "lesson_runs", "generations"} or "lesson" in low:
        cur = con.execute(f"DELETE FROM [{t}]")
        deleted[t] = cur.rowcount

# If only `lessons` exists, that's enough
if not deleted and "lessons" in tables:
    cur = con.execute("DELETE FROM lessons")
    deleted["lessons"] = cur.rowcount

con.commit()

for t in tables:
    n = con.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
    print(f"  after {t}: {n}")
print("deleted_rows:", deleted)
con.close()

# Clear generated audio files under storage/audio
removed_audio = 0
if audio_dir.is_dir():
    for p in audio_dir.rglob("*"):
        if p.is_file():
            p.unlink()
            removed_audio += 1
print("removed_audio_files:", removed_audio)
print("done")
