import sqlite3
import json
from pathlib import Path

con = sqlite3.connect("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder/backend/tutor.db")
con.row_factory = sqlite3.Row
jid = "job_9d7986e4834d4c10a1ca738c2999ee65"
row = con.execute("select * from jobs where id=?", (jid,)).fetchone()
if row:
    d = dict(row)
    print("status", d["status"], "progress", d["progress"])
    print("created", d["created_at"], "updated", d["updated_at"])
    print("error", d["error"])
    print("payload", d["payload"])
else:
    print("job missing")

# all running
print("\nALL RUNNING:")
for r in con.execute("select id, status, progress, created_at, updated_at, payload from jobs where status='running'"):
    print(dict(r))

lid = "les_f9176aba27634014a2dcc60feaeea69d"
les = con.execute(
    "select id, topic, status, created_at, updated_at, warnings, lesson_json from lessons where id=?",
    (lid,),
).fetchone()
print("\nLESSON", "FOUND" if les else "MISSING")
if les:
    print(les["id"], les["status"], les["topic"], les["created_at"], les["updated_at"])
    print("warnings", les["warnings"])
    if les["lesson_json"]:
        p = json.loads(les["lesson_json"])
        print("scenes", len(p.get("scenes") or []), "keys", list(p)[:12])

for r in con.execute(
    "select id, topic, status, created_at from lessons where lower(topic) like '%event%' or id=?",
    (lid,),
):
    print("lesson row", tuple(r))
