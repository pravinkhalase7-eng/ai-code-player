import sys, types
from pathlib import Path
sys.path.insert(0, "backend")
import app.config as cfg
cfg.settings = types.SimpleNamespace(storage_path="/tmp/aicoder_thumbs")
from app.services.images.thumbnail import write_svg_poster, _as_hook, THUMB_VERSION
print(THUMB_VERSION, _as_hook("What is a Thread?"), _as_hook("Java threads"))
out = Path(".tmp/sample_hook.svg")
out.parent.mkdir(exist_ok=True)
write_svg_poster(out, "Java threads and concurrency", "What is a Thread?", "java", None, concept_only=True)
print(out.stat().st_size)
