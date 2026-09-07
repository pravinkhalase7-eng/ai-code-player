import json, urllib.request, urllib.error
base="http://127.0.0.1:8010"
with urllib.request.urlopen(base+"/api/v1/lessons?limit=5") as r:
    lessons=(json.load(r).get("lessons") or [])
print("lessons", [(x.get("id"), x.get("topic"), x.get("status")) for x in lessons])
for it in lessons:
    lid=it.get("id")
    if not lid: continue
    req=urllib.request.Request(f"{base}/api/v1/lesson/{lid}/thumbnail?force=true", method="POST", data=b"")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            d=json.load(resp)
            print("regen", lid, (d.get("lesson") or {}).get("thumbnail_url"))
    except urllib.error.HTTPError as e:
        print("fail", lid, e.code, e.read()[:200])
