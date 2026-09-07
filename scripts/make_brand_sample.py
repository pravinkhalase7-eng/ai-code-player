import sys
from pathlib import Path
sys.path.insert(0, str(Path("backend").resolve()))
from app.services.images.thumbnail import write_svg_poster, ensure_reel_thumbnail, THUMB_VERSION

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
out_svg = Path("storage/images/thumb_brand_sample_code.svg")
write_svg_poster(
    out_svg,
    topic="Explain generics",
    title="Java Generics in 60 Seconds",
    language="java",
    code=sample_code,
    reel_mode="code",
)
s = out_svg.read_text()
print("THUMB_VERSION", THUMB_VERSION)
print("TECHSHALA BY PAVI:", "TECHSHALA BY PAVI" in s)
print("AI CODING TUTOR:", "AI CODING TUTOR" in s)

# Prefer PNG via ensure if possible
try:
    url = ensure_reel_thumbnail(
        lesson_id="brand_sample_code",
        topic="Explain generics",
        title="Java Generics in 60 Seconds",
        language="java",
        code=sample_code,
        reel_mode="code",
        force=True,
    )
    print("ensure url", url)
except TypeError as e:
    print("ensure signature mismatch", e)
    # inspect signature
    import inspect
    print(inspect.signature(ensure_reel_thumbnail))
except Exception as e:
    print("ensure failed", type(e).__name__, e)

# list outputs
for p in sorted(Path("storage/images").glob("thumb_brand_sample_code*")):
    print(p, p.stat().st_size)
