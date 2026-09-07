import sqlite3, json
from pathlib import Path
from datetime import datetime

ROOT = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder")
db = ROOT / "backend" / "tutor.db"
con = sqlite3.connect(db)
con.row_factory = sqlite3.Row
print("=== lessons (latest 8) ===")
for r in con.execute(
    "select id, topic, status, created_at, updated_at, length(lesson_json) as jl from lessons order by rowid desc limit 8"
):
    print(dict(r))

print("\n=== jobs table? ===")
tables = [r[0] for r in con.execute("select name from sqlite_master where type='table'")]
print(tables)
if "jobs" in tables:
    cols = [c[1] for c in con.execute("pragma table_info(jobs)")]
    print("job cols", cols)
    for r in con.execute("select * from jobs order by rowid desc limit 10"):
        d = dict(zip(cols, r))
        # truncate
        for k,v in list(d.items()):
            if isinstance(v,str) and len(v)>120:
                d[k]=v[:120]+"…"
        print(d)

# latest generating
rows = con.execute("select id, topic, status, lesson_json, warnings from lessons where status!='ready' order by rowid desc limit 5").fetchall()
print("\n=== non-ready ===")
for r in rows:
    print(r["id"], r["status"], r["topic"], "warn", (r["warnings"] or "")[:200])
    if r["lesson_json"]:
        try:
            p=json.loads(r["lesson_json"])
            print("  scenes", len(p.get("scenes") or []), "reel_mode", p.get("reel_mode"))
        except Exception as e:
            print("  json err", e)
con.close()
