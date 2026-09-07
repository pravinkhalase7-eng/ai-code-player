import json, urllib.request, time
from pathlib import Path

# wait briefly for reload if needed
for _ in range(10):
    try:
        with urllib.request.urlopen("http://127.0.0.1:8010/docs", timeout=2) as r:
            if r.status == 200:
                break
    except Exception:
        time.sleep(0.5)

url = "http://127.0.0.1:8010/api/v1/lesson/les_97d94b4f37b24a07bff84fe23f01c00c/thumbnail?force=true"
req = urllib.request.Request(url, method="POST", data=b"")
with urllib.request.urlopen(req, timeout=120) as resp:
    d = json.load(resp)
thumb = (d.get("lesson") or {}).get("thumbnail_url")
print("thumbnail_url:", thumb)
svg = Path("storage/images/thumb_les_97d94b4f37b24a07bff84fe23f01c00c.svg")
s = svg.read_text()
print("has TECHSHALA BY PAVI:", "TECHSHALA BY PAVI" in s)
print("has AI CODING TUTOR:", "AI CODING TUTOR" in s)
