#!/usr/bin/env python3
import importlib.util
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder")
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.schemas.lesson import DiagramStep, ConceptScene

step = DiagramStep(title="create", detail="alloc", example="Student s = new Student();")
assert step.example.startswith("Student")
scene = ConceptScene(id="c1", duration=14, narration="GC", diagram_steps=[step], bullets=["create"])
assert scene.diagram_steps[0].example

spec = importlib.util.spec_from_file_location("topic_mode_direct", BACKEND / "app/agents/topic_mode.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
instr = mod.explainer_reel_planner_instruction(30)
assert "example" in instr.lower()
assert "micro" in instr.lower() or "tiny" in instr.lower()
assert "Main.java" in instr  # still bans full programs
assert "REQUIRED" in instr or "required" in instr.lower() or "MUST" in instr

flow = (ROOT / "frontend/components/player/ExplainerFlow.tsx").read_text(encoding="utf-8")
assert "explainer-stage-card" in flow
assert "explainer-mini-pipeline" in flow
assert "explainer-example-chip" in flow
assert "<ul" not in flow or flow.count("<ul") == 0  # no stacked card list
assert "Step {" in flow or "Step $" in flow or "Step {safeActive" in flow

types = (ROOT / "frontend/types/lesson.ts").read_text(encoding="utf-8")
assert "example?: string" in types

stage = (ROOT / "frontend/components/player/ReelStage.tsx").read_text(encoding="utf-8")
assert "example: String(s.example" in stage

export = (ROOT / "frontend/lib/reelExport.ts").read_text(encoding="utf-8")
assert "ONE big active card" in export or "Focus-stage export" in export
assert "EXAMPLE" in export
# Info mode still present
assert "Info mode — violet bullets" in export

orch = (BACKEND / "app/agents/orchestrator.py").read_text(encoding="utf-8")
assert "raw_example" in orch
assert "texts.append(str(example))" in orch

conn = sqlite3.connect(BACKEND / "tutor.db")
cur = conn.cursor()
cur.execute("SELECT lesson_json FROM lessons WHERE id = ?", ("les_15a76019f0b847138917f91bd50819da",))
row = cur.fetchone()
assert row, "lesson missing"
data = json.loads(row[0])
concept = next(s for s in data["scenes"] if s["type"] == "concept")
assert all(s.get("example") for s in concept["diagram_steps"]), concept["diagram_steps"]
assert "new Student" in concept["diagram_steps"][0]["example"]
assert "null" in concept["diagram_steps"][2]["example"]
conn.close()
print("verify_explainer_focus_example OK")
