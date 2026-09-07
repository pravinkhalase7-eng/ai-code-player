import json, urllib.request
lid="les_c212bc5cac73491c94c42d877b1950a4"
with urllib.request.urlopen(f"http://127.0.0.1:8010/api/v1/lesson/{lid}", timeout=30) as r:
    d=json.load(r)
lesson=d.get("lesson") or d
print("title", lesson.get("title"))
print("mode", lesson.get("reel_mode"))
print("thumb", lesson.get("thumbnail_url"))
scenes=lesson.get("scenes") or []
print("scenes", len(scenes))
for s in scenes:
    vis=s.get("visual") or {}
    print("---", s.get("id"), "dur", s.get("duration"), "type", s.get("type"))
    print("  visual.kind", vis.get("kind"), "title", vis.get("title"))
    print("  callouts", vis.get("callouts"))
    print("  narr", (s.get("narration") or "")[:120])
