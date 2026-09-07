import json, urllib.request
lid="les_c212bc5cac73491c94c42d877b1950a4"
with urllib.request.urlopen(f"http://127.0.0.1:8010/api/v1/lesson/{lid}", timeout=30) as r:
    d=json.load(r)
lesson=d.get("lesson") or d
for s in lesson.get("scenes") or []:
    print("="*60)
    print(s.get("id"), s.get("type"), "dur", s.get("duration"))
    print("narr:", (s.get("narration") or "")[:200])
    vis=s.get("visual") or {}
    print("visual:", json.dumps(vis, indent=2)[:3000])
    segs=s.get("segments") or []
    for i,seg in enumerate(segs[:6]):
        print(f"  seg{i}", seg.get("start"), "-", seg.get("end"), ":", (seg.get("text") or "")[:100])
