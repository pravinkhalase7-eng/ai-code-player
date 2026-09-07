import json, urllib.request, sys
from pathlib import Path

# 1) Force regen current lesson thumb
lid = "les_c212bc5cac73491c94c42d877b1950a4"
url = f"http://127.0.0.1:8010/api/v1/lesson/{lid}/thumbnail?force=true"
req = urllib.request.Request(url, method="POST", data=b"")
with urllib.request.urlopen(req, timeout=120) as resp:
    d = json.load(resp)
lesson = d.get("lesson") or {}
print("lesson thumb:", lesson.get("thumbnail_url"))
print("topic:", lesson.get("topic"), "mode:", lesson.get("reel_mode"))

# 2) Local sample code poster so brand is visible on code style
sys.path.insert(0, str(Path("backend").resolve()))
from app.services.images.thumbnail import write_svg_poster, THUMB_VERSION  # noqa

sample_code = """
class Box<T> {
    private T item;
    public Box(T item) { this.item = item; }
    public T getItem() { return item; }
}
public class Main {
    public static void main(String[] args) {
        Box<String> box = new Box<>("Hello");
        String text = box.getItem();
        System.out.println(text);
    }
}
"""
out = Path("storage/images/thumb_brand_sample_code.svg")
write_svg_poster(
    out,
    topic="Explain generics",
    title="Java Generics in 60 Seconds",
    language="java",
    code=sample_code,
    reel_mode="code",
)
s = out.read_text()
print("THUMB_VERSION", THUMB_VERSION)
print("sample has TECHSHALA BY PAVI:", "TECHSHALA BY PAVI" in s)
print("sample has AI CODING TUTOR:", "AI CODING TUTOR" in s)
print("wrote", out)

# also check lesson svg if present
for p in Path("storage/images").glob(f"thumb_{lid}*"):
    if p.suffix == ".svg":
        t = p.read_text()
        print(p.name, "TECHSHALA BY PAVI:", "TECHSHALA BY PAVI" in t, "old:", "AI CODING TUTOR" in t)
