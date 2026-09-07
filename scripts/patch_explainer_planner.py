#!/usr/bin/env python3
"""Add explainer planner + wire reel_mode through orchestrator/services."""
from pathlib import Path

ROOT = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder")

# ---- topic_mode.py ----
tm = ROOT / "backend/app/agents/topic_mode.py"
tt = tm.read_text(encoding="utf-8")
if "def explainer_reel_planner_instruction" not in tt:
    tt = tt.rstrip() + """


def explainer_reel_planner_instruction(seconds: int = 30) -> str:
    target = normalize_reel_seconds(seconds)
    words_lo = int(round(target * 2.3))
    words_hi = int(round(target * 3.0))
    scale = target / 30.0

    def span(low: float, high: float) -> str:
        return f"{int(round(low * scale))}-{int(round(high * scale))}s"

    return f\"\"\"
You are the Lesson Planner Agent for an EXPLAINER reel — a mechanism diagram short (no program).
The viewer wants to understand HOW something works internally (example: how HashMap works in Java).
Create a hooky visual short. Total spoken time across ALL scenes MUST be about {target} seconds ({words_lo}-{words_hi} words total).
Set reel_seconds to {target}. Set requires_code to false. Set reel_mode to "explainer". format must be "reel".

Required scenes IN THIS ORDER: intro, concept, summary.
Do NOT include code, execution, terminal, or quiz scenes.
Do NOT invent fake code, Main.java, for-loops, put/get demos, print statements, or sandbox output.
Do NOT teach how to call an API — teach the internal mechanism stages.

Hard rules:
- Intro ({span(6, 8)}): Hook with a misconception (e.g. "HashMap is just magic O(1)"). Never open with stop scrolling.
- Concept ({span(14, 18)}): Narrate HOW it works. MUST include 4-6 diagram_steps — each is a MECHANISM stage with title + short detail.
  Example for HashMap: Key → hashCode → bucket index → store entry → collision handling → O(1) get.
  Also fill bullets with the diagram_steps titles (for older UI).
  Each diagram_step: {{"title": "...", "detail": "..."}} — title max ~6 words, detail one short clause.
- Summary ({span(4, 6)}): One punchy takeaway about the mechanism. 2-3 short takeaways. Ask them to follow / save / comment.
- Spoken style: short sentences, catchy, not a lecture. No filler.
- Never say "{target} seconds" or "in this short" in narration or titles.
- spoken_language must match the tutor plan for all spoken lines, bullets, diagram_steps, takeaways, and the title.
- lesson_id should be a short slug.
- language may stay as requested for metadata, but there is no program.
\"\"\".strip()
"""
    tm.write_text(tt + "\n", encoding="utf-8")
    print("topic_mode explainer ok")
else:
    print("topic_mode already has explainer")

# ---- orchestrator.py ----
orch = ROOT / "backend/app/agents/orchestrator.py"
ot = orch.read_text(encoding="utf-8")

ot = ot.replace(
    "from app.agents.topic_mode import explain_reel_planner_instruction, topic_requires_code",
    "from app.agents.topic_mode import (\n"
    "    explain_reel_planner_instruction,\n"
    "    explainer_reel_planner_instruction,\n"
    "    topic_requires_code,\n"
    ")",
    1,
)

# plan_lesson signature + body
old_sig = '''def plan_lesson(
    topic: str,
    language: str,
    level: str,
    format: str = "lesson",
    spoken_language: str = "en",
    reel_seconds: int = 30,
    requires_code: bool | None = None,
) -> TutorPlan:'''
new_sig = '''def plan_lesson(
    topic: str,
    language: str,
    level: str,
    format: str = "lesson",
    spoken_language: str = "en",
    reel_seconds: int = 30,
    requires_code: bool | None = None,
    reel_mode: str | None = None,
) -> TutorPlan:'''
if old_sig not in ot:
    raise SystemExit("plan_lesson signature missing")
ot = ot.replace(old_sig, new_sig, 1)

old_plan_body = '''    if fmt == "reel":
        message += (
            f"This is a {seconds}-second catchy short/reel, not a full lesson. "
            "Keep the plan tight and scale spoken depth to that length."
        )
        if requires_code is False:
            message += (
                " This is an INFO reel: requires_code=false. "
                "Do NOT plan a program. Teach the idea with intro, concept bullets, and summary only."
            )
        elif requires_code is True:
            message += " This is a CODE short: requires_code=true. Include a runnable example."
    plan = invoke_agent(TUTOR_AGENT, message)
    assert isinstance(plan, TutorPlan)
    if language:
        plan.language = language.lower()
    plan.spoken_language = locale.id
    plan.format = LessonFormat.reel if fmt == "reel" else LessonFormat.lesson
    plan.reel_seconds = seconds
    inferred = topic_requires_code(topic)
    if fmt == "reel":
        # Explicit dashboard choice wins. Only auto-detect when unset.
        if requires_code is True:
            plan.requires_code = True
        elif requires_code is False or not inferred:
            plan.requires_code = False
        else:
            plan.requires_code = bool(getattr(plan, "requires_code", True))
    else:
        plan.requires_code = True
    return plan'''

new_plan_body = '''    mode = (reel_mode or "").strip().lower() or None
    if mode not in {None, "code", "info", "explainer"}:
        mode = None
    if fmt == "reel":
        message += (
            f"This is a {seconds}-second catchy short/reel, not a full lesson. "
            "Keep the plan tight and scale spoken depth to that length."
        )
        if mode == "explainer" or (requires_code is False and mode == "explainer"):
            message += (
                " This is an EXPLAINER reel: requires_code=false, reel_mode=explainer. "
                "Do NOT plan a program. Teach HOW it works with intro, concept diagram_steps, and summary only."
            )
        elif mode == "info" or (requires_code is False and mode != "explainer"):
            message += (
                " This is an INFO reel: requires_code=false, reel_mode=info. "
                "Do NOT plan a program. Teach the idea with intro, concept bullets, and summary only."
            )
        elif mode == "code" or requires_code is True:
            message += " This is a CODE short: requires_code=true, reel_mode=code. Include a runnable example."
    plan = invoke_agent(TUTOR_AGENT, message)
    assert isinstance(plan, TutorPlan)
    if language:
        plan.language = language.lower()
    plan.spoken_language = locale.id
    plan.format = LessonFormat.reel if fmt == "reel" else LessonFormat.lesson
    plan.reel_seconds = seconds
    inferred = topic_requires_code(topic)
    if fmt == "reel":
        if mode == "explainer" or (requires_code is False and mode == "explainer"):
            plan.requires_code = False
            plan.reel_mode = "explainer"
        elif mode == "info" or (requires_code is False and mode != "explainer"):
            plan.requires_code = False
            plan.reel_mode = "info"
        elif mode == "code" or requires_code is True:
            plan.requires_code = True
            plan.reel_mode = "code"
        elif not inferred:
            plan.requires_code = False
            plan.reel_mode = "info"
        else:
            plan.requires_code = bool(getattr(plan, "requires_code", True))
            plan.reel_mode = "code" if plan.requires_code else "info"
    else:
        plan.requires_code = True
        plan.reel_mode = None
    return plan'''

if old_plan_body not in ot:
    raise SystemExit("plan_lesson body missing")
ot = ot.replace(old_plan_body, new_plan_body, 1)

# generate_structured_lesson planner selection
old_planner = '''    if is_reel and not plan.requires_code:
        planner = AgentSpec("explain_reel_planner_agent", explain_reel_planner_instruction(seconds), LessonDraft, 0.35)
    elif is_reel:
        planner = AgentSpec("reel_planner_agent", reel_planner_instruction(seconds), LessonDraft, 0.35)
    else:
        planner = PLANNER_AGENT'''
new_planner = '''    plan_mode = (getattr(plan, "reel_mode", None) or "").strip().lower()
    if is_reel and (plan_mode == "explainer" or (not plan.requires_code and plan_mode == "explainer")):
        planner = AgentSpec("explainer_reel_planner_agent", explainer_reel_planner_instruction(seconds), LessonDraft, 0.35)
    elif is_reel and not plan.requires_code:
        planner = AgentSpec("explain_reel_planner_agent", explain_reel_planner_instruction(seconds), LessonDraft, 0.35)
    elif is_reel:
        planner = AgentSpec("reel_planner_agent", reel_planner_instruction(seconds), LessonDraft, 0.35)
    else:
        planner = PLANNER_AGENT'''
if old_planner not in ot:
    raise SystemExit("planner selection missing")
ot = ot.replace(old_planner, new_planner, 1)

# Stamp reel_mode onto lesson after requires_code
if "lesson.reel_mode = getattr(plan" not in ot:
    ot = ot.replace(
        "    lesson.requires_code = bool(plan.requires_code)\n"
        "    if is_reel:\n",
        "    lesson.requires_code = bool(plan.requires_code)\n"
        "    lesson.reel_mode = getattr(plan, \"reel_mode\", None)\n"
        "    if is_reel:\n",
        1,
    )

# _normalize_reel: synthesize diagram_steps + preserve reel_mode
old_norm_tail = '''    if explain:
        cleaned = []
        for scene in scenes:
            patch: dict = {}
            if getattr(scene, "code", None):
                patch["code"] = ""
            if getattr(scene, "highlight_ranges", None):
                patch["highlight_ranges"] = []
            if getattr(scene, "expected_output", None):
                patch["expected_output"] = []
            if getattr(scene, "stdout", None):
                patch["stdout"] = []
            if getattr(scene, "stderr", None):
                patch["stderr"] = ""
            if getattr(scene, "iterations", None):
                patch["iterations"] = []
            cleaned.append(scene.model_copy(update=patch) if patch else scene)
        scenes = cleaned
    return lesson.model_copy(
        update={
            "format": LessonFormat.reel,
            "scenes": scenes,
            "code_examples": [] if explain else list(lesson.code_examples or []),
            "requires_code": False if explain else bool(lesson.requires_code),
        }
    )'''

new_norm_tail = '''    if explain:
        from app.schemas.lesson import DiagramStep

        cleaned = []
        for scene in scenes:
            patch: dict = {}
            if getattr(scene, "code", None):
                patch["code"] = ""
            if getattr(scene, "highlight_ranges", None):
                patch["highlight_ranges"] = []
            if getattr(scene, "expected_output", None):
                patch["expected_output"] = []
            if getattr(scene, "stdout", None):
                patch["stdout"] = []
            if getattr(scene, "stderr", None):
                patch["stderr"] = ""
            if getattr(scene, "iterations", None):
                patch["iterations"] = []
            if scene.type == "concept":
                steps = list(getattr(scene, "diagram_steps", None) or [])
                bullets = list(getattr(scene, "bullets", None) or [])
                if not steps and bullets:
                    patch["diagram_steps"] = [
                        DiagramStep(title=str(b)[:120], detail="") for b in bullets if str(b).strip()
                    ]
                elif steps and not bullets:
                    patch["bullets"] = [
                        (getattr(s, "title", None) or (s.get("title") if isinstance(s, dict) else str(s)))[:120]
                        for s in steps
                    ]
            cleaned.append(scene.model_copy(update=patch) if patch else scene)
        scenes = cleaned
    mode = getattr(lesson, "reel_mode", None)
    if explain and not mode:
        mode = "info"
    if not explain:
        mode = mode or "code"
    return lesson.model_copy(
        update={
            "format": LessonFormat.reel,
            "scenes": scenes,
            "code_examples": [] if explain else list(lesson.code_examples or []),
            "requires_code": False if explain else bool(lesson.requires_code),
            "reel_mode": mode,
        }
    )'''

if old_norm_tail not in ot:
    raise SystemExit("_normalize_reel tail missing")
ot = ot.replace(old_norm_tail, new_norm_tail, 1)

orch.write_text(ot, encoding="utf-8")
print("orchestrator ok")
print("done")
