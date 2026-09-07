import json
from pathlib import Path
root = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder/storage")
for path in sorted(root.glob("tmp-les_*.json")):
    d = json.loads(path.read_text())
    L = d["lesson"]
    print("\n====", L.get("lesson_id"), L.get("topic"))
    print("reel_mode=", L.get("reel_mode"), "format=", L.get("format"), "requires_code=", L.get("requires_code"))
    for s in L.get("scenes") or []:
        narr = (s.get("narration") or "").replace("\n", " ")
        code = (s.get("code") or "").replace("\n", " ")
        print(f"  [{s.get('type')}] {narr[:220]}")
        if code.strip():
            print(f"    CODE: {code[:180]}")
