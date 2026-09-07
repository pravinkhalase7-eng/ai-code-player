from pathlib import Path
import ast

path = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder/backend/app/services/images/thumbnail.py")
text = path.read_text()
old = 'AI CODING TUTOR'
new = 'TECHSHALA BY PAVI'
count = text.count(old)
if count < 1:
    raise SystemExit(f'brand text not found, count={count}')
text = text.replace(old, new)
# bump version
if 'THUMB_VERSION = "tilt-v13-fullcode"' in text:
    text = text.replace('THUMB_VERSION = "tilt-v13-fullcode"', 'THUMB_VERSION = "tilt-v14-brand"', 1)
elif 'THUMB_VERSION =' in text:
    import re
    text2, n = re.subn(r'THUMB_VERSION = "[^"]+"', 'THUMB_VERSION = "tilt-v14-brand"', text, count=1)
    if n != 1:
        raise SystemExit('version bump failed')
    text = text2
path.write_text(text)
ast.parse(text)
print(f'replaced {count} occurrence(s); version tilt-v14-brand')
