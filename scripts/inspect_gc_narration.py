import json
from pathlib import Path
l = json.loads(Path("/tmp/les_gc.json").read_text())["lesson"]
c = next(s for s in l["scenes"] if s["type"] == "concept")
nar = c["narration"]
print("FULL NARRATION:")
print(nar)
print("---LEN", len(nar))
print("HEAP COUNT", nar.count("Heap Allocation"))
print("diagram_steps", c.get("diagram_steps"))
print("bullets", c.get("bullets"))
print("audio", c.get("audio_url"))
idx = nar.find("Heap Allocation")
print("first Heap at", idx)
if idx >= 0:
    print(repr(nar[max(0, idx - 80) : idx + 250]))
