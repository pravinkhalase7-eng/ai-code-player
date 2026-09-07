import json
import time
import urllib.request
import sqlite3

lid = "les_492016b5b907465bae21cd8ff5e87218"
jid = "job_1d1ba31b6ce347aa9451e3d6008f4e21"
for i in range(24):
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:8010/api/v1/lesson/{lid}", timeout=5) as resp:
            d = json.loads(resp.read().decode())
            print(i, "api", d.get("status"), "scenes", len((d.get("lesson") or {}).get("scenes") or []), "warn", (d.get("warnings") or [])[:1])
            if d.get("status") in {"ready", "failed"}:
                break
    except Exception as e:
        print(i, "api_err", e)
    con = sqlite3.connect("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder/backend/tutor.db")
    job = con.execute("select status, progress, error from jobs where id=?", (jid,)).fetchone()
    les = con.execute("select status from lessons where id=?", (lid,)).fetchone()
    print(i, "db job", job, "lesson", les)
    con.close()
    time.sleep(2.5)
else:
    print("still not done")
