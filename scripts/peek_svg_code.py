from pathlib import Path
s = Path("storage/images/thumb_les_97d94b4f37b24a07bff84fe23f01c00c.svg").read_text()
# extract code text lines
import re
texts = re.findall(r'<text[^>]*xml:space="preserve"[^>]*>(.*?)</text>', s)
for t in texts:
    print(t)
print("---ellipsis count", s.count("…") + s.count("&#8230;"))
