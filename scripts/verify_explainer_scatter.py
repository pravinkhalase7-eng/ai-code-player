#!/usr/bin/env python3
import importlib.util
import sys
from pathlib import Path

BACKEND = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder/backend")
sys.path.insert(0, str(BACKEND))

from app.schemas.lesson import ConceptScene, DiagramStep, IntroScene, Lesson, SummaryScene

# Load only gather/scatter via exec from orchestrator source is heavy; reimplement check by importing functions
# Avoid agents.__init__ by loading orchestrator after stubbing gemini
import types
gemini = types.ModuleType("app.services.gemini_client")
gemini.generate_text = lambda *a, **k: ""
gemini.structured_generate = lambda *a, **k: None
sys.modules["app.services.gemini_client"] = gemini
sys.modules["google"] = types.ModuleType("google")
sys.modules["google.genai"] = types.ModuleType("google.genai")

from app.agents.orchestrator import gather_teaching_texts, scatter_teaching_texts

lesson = Lesson(
    lesson_id="les_x",
    title="HashMap",
    language="java",
    topic="how hashmap works in java",
    objectives=["Understand buckets"],
    format="reel",
    requires_code=False,
    reel_mode="explainer",
    scenes=[
        IntroScene(id="i", duration=6, narration="Hook line"),
        ConceptScene(
            id="c",
            duration=14,
            narration="Mechanism",
            bullets=["Key", "hashCode"],
            diagram_steps=[
                DiagramStep(title="Key", detail="input object"),
                DiagramStep(title="hashCode", detail=""),
            ],
        ),
        SummaryScene(id="s", duration=5, narration="Done", takeaways=["O(1) lookup"]),
    ],
)
texts = gather_teaching_texts(lesson)
# Mutate slightly
translated = [f"T:{t}" for t in texts]
out = scatter_teaching_texts(lesson, translated)
assert out.title.startswith("T:")
concept = next(s for s in out.scenes if s.type == "concept")
assert concept.diagram_steps[0].title.startswith("T:")
assert concept.diagram_steps[0].detail.startswith("T:")
assert concept.diagram_steps[1].title.startswith("T:")
assert concept.diagram_steps[1].detail == ""  # empty detail not translated
assert concept.bullets[0].startswith("T:")
print("scatter roundtrip ok", len(texts))
