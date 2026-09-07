import json, sqlite3
con = sqlite3.connect("backend/tutor.db")
row = con.execute("select lesson_json from lessons where id=?", ("les_ed73d65547a3412da97fd5f02d10c092",)).fetchone()
raw = row[0]
lesson = raw if isinstance(raw, dict) else json.loads(raw)
# if double-encoded string
if isinstance(lesson, str):
    lesson = json.loads(lesson)
for scene in lesson.get("scenes") or []:
    if scene.get("type") != "concept":
        continue
    print("narration_len_before", len(scene.get("narration") or ""))
    segs = scene.get("segments") or []
    # rebuild short narration from segment texts
    texts = [str(s.get("text") or "").strip() for s in segs if str(s.get("text") or "").strip()]
    narration = " ".join(texts)
    if len(narration) > 1900:
        narration = narration[:1900]
    scene["narration"] = narration
    scene["duration"] = 34.5
    vd = scene.get("visual_diagram") or {}
    vd.update({
        "kind": "hashmap",
        "capacity": 8,
        "init_code": "Map<String, Integer> map = new HashMap<>();",
        "setup_lines": ["// Capacity = 8 buckets"],
        "puts": [
            {"code": 'map.put("Mia", 100);', "key": "Mia", "value": "100", "hash_bits": "01001011", "bucket": 3, "color": "orange"},
            {"code": 'map.put("Leo", 300);', "key": "Leo", "value": "300", "hash_bits": "00110011", "bucket": 3, "color": "green"},
        ],
        "node_fields": ["key", "value", "hash", "next"],
    })
    scene["visual_diagram"] = vd
    print("narration_len_after", len(narration))
    print("narration", narration[:200])
# store as dict-friendly JSON string; SQLAlchemy JSON accepts str that is valid json or dict depending on driver
con.execute("update lessons set lesson_json=? where id=?", (json.dumps(lesson, ensure_ascii=False), "les_ed73d65547a3412da97fd5f02d10c092"))
con.commit()
# validate with pydantic
import sys
sys.path.insert(0, "backend")
from app.schemas.lesson import Lesson
Lesson.model_validate(lesson)
print("validated ok")
con.close()
