import json, sqlite3
from pathlib import Path

# Fix HashMapBoard preview for hash/index
board = Path("frontend/components/player/HashMapBoard.tsx")
bt = board.read_text()
old = """  const activePut = safeActive >= 0 ? puts[safeActive] : null;
  const colliding = activePut ? isCollision(puts, safeActive) : false;
  const showEquals = Boolean(activePut && colliding && p >= 0.35 && p < 0.72);
  const formulaBucket = activePut?.bucket;"""
new = """  const activePut = safeActive >= 0 ? puts[safeActive] : null;
  // During hash/index phases keep formula+first put preview so the board is never blank.
  const previewPut = !activePut && (phaseKind === "hash" || phaseKind === "index" || phaseKind === "other") ? puts[0] || null : null;
  const focusPut = activePut || previewPut;
  const colliding = activePut ? isCollision(puts, safeActive) : false;
  const showEquals = Boolean(activePut && colliding && p >= 0.2 && p < 0.85);
  const formulaBucket = focusPut?.bucket;"""
if old not in bt:
    print("board formula block missing, skip")
else:
    bt = bt.replace(old, new, 1)
    bt = bt.replace("activePut?.hash_bits", "focusPut?.hash_bits")
    # highlight first put pill while previewing
    bt = bt.replace(
        "const active = index === safeActive;\n            const past = index < safeActive;",
        "const active = index === safeActive || (safeActive < 0 && previewPut && index === 0);\n            const past = index < safeActive;",
    )
    board.write_text(bt)
    print("HashMapBoard preview ok")

# Patch lesson DB
con = sqlite3.connect("backend/tutor.db")
row = con.execute("select lesson_json from lessons where id=?", ("les_ed73d65547a3412da97fd5f02d10c092",)).fetchone()
if not row:
    raise SystemExit("lesson missing")
lesson = row[0] if isinstance(row[0], dict) else json.loads(row[0])
for scene in lesson.get("scenes") or []:
    if scene.get("type") != "concept":
        continue
    scene["duration"] = 34.5
    vd = scene.get("visual_diagram") or {"kind": "hashmap", "capacity": 8, "node_fields": ["key", "value", "hash", "next"]}
    vd["kind"] = "hashmap"
    vd["capacity"] = 8
    vd["init_code"] = "Map<String, Integer> map = new HashMap<>();"
    vd["setup_lines"] = ["// Capacity = 8 buckets"]
    vd["puts"] = [
        {"code": 'map.put("Mia", 100);', "key": "Mia", "value": "100", "hash_bits": "01001011", "bucket": 3, "color": "orange"},
        {"code": 'map.put("Leo", 300);', "key": "Leo", "value": "300", "hash_bits": "00110011", "bucket": 3, "color": "green"},
    ]
    vd["node_fields"] = ["key", "value", "hash", "next"]
    scene["visual_diagram"] = vd
    # keep segments; ensure ends aligned
    segs = scene.get("segments") or []
    if len(segs) >= 5:
        bounds = [(0,7),(7,14),(14,20),(20,27),(27,34.5)]
        for i,(a,b) in enumerate(bounds):
            segs[i]["start"] = a
            segs[i]["end"] = b
        scene["segments"] = segs[:5]
con.execute("update lessons set lesson_json=? where id=?", (json.dumps(lesson, ensure_ascii=False), "les_ed73d65547a3412da97fd5f02d10c092"))
con.commit()
con.close()
print("lesson patched duration=34.5 puts=Mia,Leo")
