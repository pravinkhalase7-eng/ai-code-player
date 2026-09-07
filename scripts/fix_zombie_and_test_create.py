import sqlite3
import json
import urllib.request
from pathlib import Path

DB = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder/backend/tutor.db")
con = sqlite3.connect(DB)
# fail zombie jobs
cur = con.execute(
    "update jobs set status='failed', error=?, updated_at=datetime('now') where status in ('running','queued') and created_at < datetime('now','-1 hour')",
    ("Stale job cleared — lesson was deleted or worker died.",),
)
print("cleared stale jobs", cur.rowcount)
con.commit()
print("remaining open", list(con.execute("select id,status from jobs where status in ('running','queued')")))
con.close()

# probe create endpoint (may take a while if Gemini)
body = json.dumps({
    "topic": "what is a variable in java",
    "language": "java",
    "level": "beginner",
    "format": "reel",
    "spoken_language": "en",
    "reel_seconds": 30,
    "requires_code": False,
    "reel_mode": "info",
}).encode()
req = urllib.request.Request(
    "http://127.0.0.1:8010/api/v1/tutor/lesson",
    data=body,
    headers={"Content-Type": "application/json"},
    method="POST",
)
print("posting create…")
try:
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = resp.read().decode()
        print("create status", resp.status, raw[:400])
except Exception as e:
    print("create error", type(e).__name__, e)
