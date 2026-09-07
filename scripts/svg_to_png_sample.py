import sys
from pathlib import Path
sys.path.insert(0, str(Path("backend").resolve()))
from app.services.images.thumbnail import write_svg_poster

# Find raster helper
import app.services.images.thumbnail as th
names = [n for n in dir(th) if "png" in n.lower() or "raster" in n.lower() or "render" in n.lower() or "cairo" in n.lower() or "svg" in n.lower()]
print("helpers", names)

svg = Path("storage/images/thumb_brand_sample_code.svg")
png = Path("storage/images/thumb_brand_sample_code.png")

# try common approaches used in this file
src = Path("backend/app/services/images/thumbnail.py").read_text()
for needle in ["cairosvg", "rsvg", "qlmanage", "convert", "PIL", "svglib", "wand"]:
    if needle in src:
        print("uses", needle)

# Call ensure path that writes both - look at ensure_reel_thumbnail body
import inspect
print(inspect.getsource(th.ensure_reel_thumbnail)[:2500])
