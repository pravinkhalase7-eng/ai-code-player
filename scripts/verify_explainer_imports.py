#!/usr/bin/env python3
import importlib.util
import sys
from pathlib import Path

BACKEND = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder/backend")
sys.path.insert(0, str(BACKEND))

# Import schemas without pulling gemini via agents.__init__
from app.schemas.lesson import ConceptScene, DiagramStep, Lesson, TutorPlan, LessonDraft
from app.schemas.api import LessonCreateRequest

# Load topic_mode directly
spec = importlib.util.spec_from_file_location(
    "topic_mode_direct",
    BACKEND / "app/agents/topic_mode.py",
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

req = LessonCreateRequest(topic="how hashmap works in java", format="reel", requires_code=False, reel_mode="explainer")
assert req.reel_mode == "explainer"
step = DiagramStep(title="hashCode", detail="maps key to int")
scene = ConceptScene(id="c1", duration=14, narration="How hashmap works", diagram_steps=[step], bullets=["hashCode"])
assert scene.diagram_steps[0].title == "hashCode"
plan = TutorPlan(
    language="java",
    topic="how hashmap works in java",
    title="HashMap internals",
    objectives=["Understand hashing"],
    concepts=["hashCode", "buckets"],
    greeting="Lets dig in",
    requires_code=False,
    reel_mode="explainer",
    format="reel",
)
assert plan.reel_mode == "explainer"
draft = LessonDraft(
    lesson_id="les_test",
    title="HashMap",
    language="java",
    topic="how hashmap works in java",
    objectives=["x"],
    scenes=[
        {"id": "i", "type": "intro", "duration": 6, "narration": "Hook"},
        {
            "id": "c",
            "type": "concept",
            "duration": 14,
            "narration": "Mechanism",
            "bullets": ["a", "b"],
            "diagram_steps": [{"title": "a", "detail": "d"}],
        },
        {"id": "s", "type": "summary", "duration": 5, "narration": "Done", "takeaways": ["t"]},
    ],
    requires_code=False,
    reel_mode="explainer",
    format="reel",
)
assert draft.reel_mode == "explainer"
text = mod.explainer_reel_planner_instruction(30)
assert "diagram_steps" in text and "explainer" in text
# Spot-check orchestrator source without importing gemini
orch = (BACKEND / "app/agents/orchestrator.py").read_text(encoding="utf-8")
assert "explainer_reel_planner_instruction" in orch
assert 'plan_mode == "explainer"' in orch
assert 'patch["diagram_steps"]' in orch
print("ok")
