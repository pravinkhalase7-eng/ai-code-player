import json, urllib.request
url = "http://127.0.0.1:8010/api/v1/lesson/les_97d94b4f37b24a07bff84fe23f01c00c/thumbnail?force=true"
req = urllib.request.Request(url, method="POST", data=b"")
with urllib.request.urlopen(req, timeout=120) as resp:
    d = json.load(resp)
print("thumbnail_url:", d.get("thumbnail_url"))
print("topic:", d.get("topic"))
print("reel_mode:", d.get("reel_mode"))
