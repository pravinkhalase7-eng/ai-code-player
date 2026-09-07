import json, urllib.request, urllib.error, time
from pathlib import Path

base = "http://127.0.0.1:8010"
# health
try:
    with urllib.request.urlopen(base + "/docs", timeout=3) as r:
        print("docs", r.status)
except Exception as e:
    print("docs fail", e)

# list lessons
try:
    with urllib.request.urlopen(base + "/api/v1/lessons?limit=20", timeout=10) as r:
        d = json.load(r)
    lessons = d.get("lessons") or []
    print("lessons", len(lessons))
    for it in lessons:
        print(it.get("id") or it.get("lesson_id"), it.get("topic"), it.get("reel_mode"))
except Exception as e:
    print("list fail", e)

# try openapi path for thumbnail
try:
    with urllib.request.urlopen(base + "/openapi.json", timeout=10) as r:
        o = json.load(r)
    paths = [p for p in o.get("paths", {}) if "thumbnail" in p]
    print("thumb paths:", paths)
except Exception as e:
    print("openapi fail", e)

lid = "les_97d94b4f37b24a07bff84fe23f01c00c"
for path in [
    f"/api/v1/lesson/{lid}/thumbnail?force=true",
    f"/api/v1/lessons/{lid}/thumbnail?force=true",
]:
    url = base + path
    req = urllib.request.Request(url, method="POST", data=b"")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            d = json.load(resp)
            print("OK", path, (d.get("lesson") or {}).get("thumbnail_url"))
    except urllib.error.HTTPError as e:
        print("HTTP", e.code, path, e.read()[:300])
    except Exception as e:
        print("ERR", path, e)
