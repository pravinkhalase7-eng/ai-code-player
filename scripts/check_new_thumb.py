import json, urllib.request
from pathlib import Path

url = "http://127.0.0.1:8010/api/v1/lesson/les_97d94b4f37b24a07bff84fe23f01c00c/thumbnail?force=true"
req = urllib.request.Request(url, method="POST", data=b"")
with urllib.request.urlopen(req, timeout=120) as resp:
    d = json.load(resp)
lesson = d.get("lesson") or {}
thumb = lesson.get("thumbnail_url")
print("thumbnail_url:", thumb)

# locate files
img_dir = Path("storage/images")
if not img_dir.exists():
    img_dir = Path("backend/storage/images")
print("img_dir", img_dir, "exists", img_dir.exists())
for p in sorted(img_dir.glob("thumb_les_97d94b4f37b24a07bff84fe23f01c00c*")):
    print(p.name, p.stat().st_size, p.stat().st_mtime)

# check svg for underline rect y=1640
for p in sorted(img_dir.glob("thumb_les_97d94b4f37b24a07bff84fe23f01c00c*")):
    if p.suffix == ".svg":
        s = p.read_text()
        print("has y=\"1640\"", 'y="1640"' in s)
        print("has techshalabypavi", "techshalabypavi" in s)
        # sample a long code line
        for line in s.splitlines():
            if "Box" in line or "…" in line or "&#8230;" in line:
                print(line[:180])
