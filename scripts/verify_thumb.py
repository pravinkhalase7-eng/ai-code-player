from pathlib import Path
import sys
ROOT = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder")
sys.path.insert(0, str(ROOT / "backend"))
from app.services.images.thumbnail import write_svg_poster, THUMB_VERSION, _diagram_kind

print(THUMB_VERSION)
print("kinds", _diagram_kind("how hashmap works", "explainer"), _diagram_kind("garbage collection", "explainer"))
p = ROOT / "storage/images/thumb_preview_hashmap.svg"
write_svg_poster(
    p,
    "how hashmap works internally in java",
    "how hashmap works internally in java",
    "java",
    None,
    reel_mode="explainer",
)
body = p.read_text()
print("bytes", p.stat().st_size)
print("HASHMAP", "HASHMAP" in body)
print("concept only", "concept only" in body)
print("EXPLAINER", "EXPLAINER" in body)
lesson = ROOT / "storage/images/thumb_les_9aa6c519210a47a3b86e54fbf31419d3.svg"
if lesson.is_file():
    b = lesson.read_text()
    print("lesson HASHMAP", "HASHMAP" in b, "concept only", "concept only" in b)
