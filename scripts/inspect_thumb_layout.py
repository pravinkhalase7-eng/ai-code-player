from pathlib import Path
import re
ROOT = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder")
p = ROOT / "storage/images/thumb_les_34b2b09e272f43e389c24afcbfafc655.svg"
body = p.read_text()
print("len", len(body))
# extract card y/height and whether diagram transform is inside/outside card
for m in re.finditer(r'<rect x="72" y="(\d+)" rx="28" width="936" height="(\d+)"', body):
    print("card y,h", m.group(1), m.group(2))
for m in re.finditer(r'transform="translate\((\d+),\s*(\d+)\)"', body):
    print("translate", m.group(1), m.group(2))
# show snippet around diagram
idx = body.find("GC")
print(body[max(0,idx-200):idx+400])
print("---")
# How images served?
grep = ROOT / "backend/app"
import subprocess
r = subprocess.run(["grep","-rn","/images","backend/app","--include=*.py"], cwd=ROOT, capture_output=True, text=True)
print(r.stdout[:1500])
