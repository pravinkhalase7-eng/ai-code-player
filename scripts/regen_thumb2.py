import json, urllib.request, urllib.error
url = "http://127.0.0.1:8010/api/v1/lesson/les_97d94b4f37b24a07bff84fe23f01c00c/thumbnail?force=true"
req = urllib.request.Request(url, method="POST", data=b"")
try:
    with urllib.request.urlopen(req, timeout=120) as resp:
        raw = resp.read().decode()
        print("status", resp.status)
        print(raw[:2000])
except urllib.error.HTTPError as e:
    print("HTTP", e.code)
    print(e.read().decode()[:2000])

# also check endpoint signature
from pathlib import Path
text = Path("backend/app/api/v1/router.py").read_text()
i = text.find("def post_thumbnail")
print("---endpoint---")
print(text[i:i+600])
