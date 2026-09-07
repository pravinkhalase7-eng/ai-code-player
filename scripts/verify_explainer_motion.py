from pathlib import Path
ROOT = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder")
rs = (ROOT / "frontend/components/player/ReelStage.tsx").read_text()
assert "isPosterScene(scene.type) && !explainMotion" in rs
assert "synthesizeBoardSteps" in rs
ex = (ROOT / "frontend/lib/reelExport.ts").read_text()
assert "synthesizeBoardSteps(scene, lesson)" in ex
assert "isExplainMotionLesson" in ex
th = (ROOT / "backend/app/services/images/thumbnail.py").read_text()
assert "tilt-v15-viral" in th
assert "_svg_python_why_v8" in th
svg = (ROOT / "storage/images/thumb_les_c212bc5cac73491c94c42d877b1950a4.svg").read_text()
assert "WHY PYTHON?" in svg
assert "TECHSHALA BY PAVI" in svg
print("assertions_ok")
