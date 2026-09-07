import json, urllib.request, urllib.error
base="http://127.0.0.1:8010"
with urllib.request.urlopen(base+"/api/v1/lessons?limit=5") as r:
    raw=r.read().decode()
print(raw[:800])
d=json.loads(raw)
lessons=d.get("lessons") or []
for it in lessons:
    print("keys", sorted(it.keys()))
    lid = it.get("lesson_id") or it.get("id")
    print("lid", lid, "status", it.get("status"), "topic", it.get("topic"))
    if not lid:
        continue
    req=urllib.request.Request(f"{base}/api/v1/lesson/{lid}/thumbnail?force=true", method="POST", data=b"")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            out=json.load(resp)
            print("thumb", (out.get("lesson") or {}).get("thumbnail_url"))
    except urllib.error.HTTPError as e:
        print("HTTP", e.code, e.read()[:400])
