import json, urllib.request
lid="les_c212bc5cac73491c94c42d877b1950a4"
with urllib.request.urlopen(f"http://127.0.0.1:8010/api/v1/lesson/{lid}", timeout=30) as r:
    d=json.load(r)
lesson=d.get("lesson") or d
for s in lesson.get("scenes") or []:
    print(s.get("type"), "diagram_steps:", json.dumps(s.get("diagram_steps"), indent=2)[:1500])
    print("bullets:", s.get("bullets"))
    print("takeaways:", s.get("takeaways"))
