import json, urllib.request
lid="les_c212bc5cac73491c94c42d877b1950a4"
with urllib.request.urlopen(f"http://127.0.0.1:8010/api/v1/lesson/{lid}") as r:
    d=json.load(r)
lesson=d.get("lesson") or d
for s in lesson.get("scenes") or []:
    if s.get("type")=="concept":
        for step in s.get("diagram_steps") or []:
            print(repr(step.get("title")))
        print("bullets", s.get("bullets"))
