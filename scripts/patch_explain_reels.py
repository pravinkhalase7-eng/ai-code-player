from pathlib import Path
import re

ROOT = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder")

# ---- schema ----
schema = ROOT / "backend/app/schemas/lesson.py"
text = schema.read_text(encoding="utf-8")
if "requires_code: bool = True" not in text:
    text = text.replace(
        '    greeting: str = Field(min_length=1, max_length=400)\n    reel_seconds: int = 30\n\n    @field_validator("spoken_language")',
        '    greeting: str = Field(min_length=1, max_length=400)\n    reel_seconds: int = 30\n    requires_code: bool = True\n\n    @field_validator("spoken_language")',
        1,
    )
    text = text.replace(
        '    thumbnail_url: str | None = None\n    reel_seconds: int = 30\n\n    @field_validator("language")',
        '    thumbnail_url: str | None = None\n    reel_seconds: int = 30\n    requires_code: bool = True\n\n    @field_validator("language")',
        1,
    )
old_v = '''    def _required_scene_types(self) -> Lesson:
        types = {scene.type for scene in self.scenes}
        if self.format == LessonFormat.reel:
            missing = {"intro", "code", "summary"} - types
        else:
            missing = {"intro", "code", "quiz"} - types
        if missing:
            raise ValueError(f"lesson is missing required scenes: {sorted(missing)}")
        return self'''
new_v = '''    def _required_scene_types(self) -> Lesson:
        types = {scene.type for scene in self.scenes}
        if self.format == LessonFormat.reel:
            if self.requires_code is False or ("code" not in types and "concept" in types):
                missing = {"intro", "concept", "summary"} - types
            else:
                missing = {"intro", "code", "summary"} - types
        else:
            missing = {"intro", "code", "quiz"} - types
        if missing:
            raise ValueError(f"lesson is missing required scenes: {sorted(missing)}")
        return self'''
if old_v not in text:
    raise SystemExit("validator block missing")
text = text.replace(old_v, new_v, 1)
if "if data.get(\"requires_code\") is False:" not in text:
    text = text.replace(
        "def fill_empty_scene_code(data: dict) -> dict:\n",
        "def fill_empty_scene_code(data: dict) -> dict:\n"
        "    if data.get(\"requires_code\") is False:\n"
        "        return data\n"
        "    scene_types = {scene.get(\"type\") for scene in (data.get(\"scenes\") or []) if isinstance(scene, dict)}\n"
        "    if data.get(\"format\") == \"reel\" and \"code\" not in scene_types and \"execution\" not in scene_types:\n"
        "        return data\n",
        1,
    )
# LessonDraft may also need requires_code - check
if "class LessonDraft" in text and "requires_code" not in text[text.index("class LessonDraft"):text.index("class LessonDraft")+800]:
    text = text.replace(
        "class LessonDraft(BaseModel):\n",
        "class LessonDraft(BaseModel):\n    # drafts may omit requires_code; Lesson validator infers from scenes\n",
        1,
    )
schema.write_text(text, encoding="utf-8")
print("schema ok")

# ---- orchestrator ----
orch = ROOT / "backend/app/agents/orchestrator.py"
ot = orch.read_text(encoding="utf-8")

helper = '''
def topic_requires_code(topic: str) -> bool:
    """False for conceptual / AI literacy topics that cannot be a runnable program."""
    text = (topic or "").strip()
    blob = text.casefold()
    coding_hints = (
        "loop", "variable", "function", "class", "array", "string", "python", "java",
        "javascript", "code", "program", "sql", "html", "css", "react", "algorithm",
        "sort", "recursion", "pointer", "thread", "async", "promise", "callback",
        "api", "method", "object", "list", "dict", "tuple", "set", "boolean",
        "compile", "runtime", "debug", "regex", "json", "http", "server", "database",
        "for loop", "while", "if else", "switch", "map", "filter", "stream",
    )
    concept_hints = (
        "large language model", "language model", " llm", "llm ", "chatgpt", "gpt-",
        "transformer", "neural network", "machine learning", "deep learning",
        "artificial intelligence", "what is ai", "prompt engineering", "tokenizer",
        "attention mechanism", "foundation model", "generative ai", "agi",
        "diffusion model", "embedding", "vector database", "rag ", " halluci",
    )
    has_coding = any(h in blob for h in coding_hints)
    has_concept = any(h in blob for h in concept_hints)
    if has_concept and not has_coding:
        return False
    if re.match(r"^(what is|what's|whats|explain|define)\\b", blob) and not has_coding:
        return False
    return True


def explain_reel_planner_instruction(seconds: int = 30) -> str:
    target = normalize_reel_seconds(seconds)
    words_lo = int(round(target * 2.3))
    words_hi = int(round(target * 3.0))
    scale = target / 30.0

    def span(low: float, high: float) -> str:
        return f"{int(round(low * scale))}-{int(round(high * scale))}s"

    return f"""
You are the Lesson Planner Agent for an explain-only coding-literacy reel (no program).
The topic cannot be demonstrated with a tiny runnable program (example: what is a large language model).
Create a hooky visual short. Total spoken time across ALL scenes MUST be about {target} seconds ({words_lo}-{words_hi} words total).
Set reel_seconds to {target}. Set requires_code to false. format must be "reel".

Required scenes IN THIS ORDER: intro, concept, summary.
Do NOT include code, execution, terminal, or quiz scenes.
Do NOT invent fake code, Main.java, print statements, or sandbox output.

Hard rules:
- Intro ({span(6, 8)}): Hook in the first sentence. Name the idea with a question or common misconception. Never open with stop scrolling.
- Concept ({span(14, 18)}): Teach the idea clearly in spoken sentences. Include 4-6 short bullets that a viewer can read on screen (definitions, parts, why it matters).
- Summary ({span(4, 6)}): One punchy takeaway. 2-3 short takeaways. Ask them to follow / save / comment.
- Spoken style: short sentences, catchy, not a lecture. No filler.
- Never say "{target} seconds" or "in this short" in narration or titles.
- spoken_language must match the tutor plan for all spoken lines, bullets, takeaways, and the title.
- lesson_id should be a short slug.
- language may stay as requested for metadata, but there is no program.
""".strip()

'''

if "def topic_requires_code(" not in ot:
    # insert before plan_lesson / _language_from_topic
    anchor = "def _language_from_topic(topic: str, selected: str) -> str:"
    if anchor not in ot:
        raise SystemExit("anchor _language_from_topic missing")
    ot = ot.replace(anchor, helper + "\n\n" + anchor, 1)

# Tutor instruction addition
if "requires_code" not in ot[ot.index("TUTOR_INSTRUCTION"):ot.index("TUTOR_INSTRUCTION")+1200]:
    ot = ot.replace(
        "Never claim that code ran. Never invent terminal output.\n\"\"\".strip()",
        "Never claim that code ran. Never invent terminal output.\n"
        "Set requires_code=false when the topic is conceptual and cannot be a runnable program "
        "(large language models, neural nets, what is AI, prompt engineering, transformers, etc.).\n"
        "Set requires_code=true for programming topics (loops, variables, functions, APIs, frameworks).\n"
        "\"\"\".strip()",
        1,
    )

# plan_lesson: force requires_code from heuristic + agent
old_plan_tail = '''    plan = invoke_agent(TUTOR_AGENT, message)
    assert isinstance(plan, TutorPlan)
    if language:
        plan.language = language.lower()
    plan.spoken_language = locale.id
    plan.format = LessonFormat.reel if fmt == "reel" else LessonFormat.lesson
    plan.reel_seconds = seconds
    return plan'''

new_plan_tail = '''    plan = invoke_agent(TUTOR_AGENT, message)
    assert isinstance(plan, TutorPlan)
    if language:
        plan.language = language.lower()
    plan.spoken_language = locale.id
    plan.format = LessonFormat.reel if fmt == "reel" else LessonFormat.lesson
    plan.reel_seconds = seconds
    # Conceptual topics become explain-only reels (or lessons without forced sandbox demos).
    inferred = topic_requires_code(topic)
    if fmt == "reel":
        plan.requires_code = bool(getattr(plan, "requires_code", True)) and inferred
        if not inferred:
            plan.requires_code = False
    else:
        plan.requires_code = True
    return plan'''

if old_plan_tail not in ot:
    raise SystemExit("plan_lesson tail missing")
ot = ot.replace(old_plan_tail, new_plan_tail, 1)

# generate_structured_lesson: choose explain planner; skip code agents; stamp requires_code
ot = ot.replace(
    '    planner = (\n        AgentSpec("reel_planner_agent", reel_planner_instruction(seconds), LessonDraft, 0.35)\n        if is_reel\n        else PLANNER_AGENT\n    )',
    '    if is_reel and not plan.requires_code:\n'
    '        planner = AgentSpec("explain_reel_planner_agent", explain_reel_planner_instruction(seconds), LessonDraft, 0.35)\n'
    '    elif is_reel:\n'
    '        planner = AgentSpec("reel_planner_agent", reel_planner_instruction(seconds), LessonDraft, 0.35)\n'
    '    else:\n'
    '        planner = PLANNER_AGENT',
    1,
)

# After lesson created, stamp requires_code early - find lesson.topic = plan.topic block
if "lesson.requires_code = plan.requires_code" not in ot:
    ot = ot.replace(
        "    lesson.topic = plan.topic\n    lesson.reel_seconds = seconds\n",
        "    lesson.topic = plan.topic\n    lesson.reel_seconds = seconds\n    lesson.requires_code = bool(plan.requires_code)\n",
        1,
    )

# Skip CODE/VISUAL agents for explain reels
old_agents = '''    spoken_rules = f"{spoken_generation_rules(plan.spoken_language)}\\n{CODE_TEACHING_RULES}"
    if not has_code or empty_main:
        lesson = invoke_agent(CODE_AGENT, f"{spoken_rules}\\n{lesson.model_dump_json()}")
        assert isinstance(lesson, Lesson)
        lesson.spoken_language = plan.spoken_language
    has_highlights = any(
        getattr(scene, "highlight_ranges", None) for scene in lesson.scenes if scene.type == "code"
    )
    if not has_highlights:
        lesson = invoke_agent(VISUAL_AGENT, f"{spoken_rules}\\n{lesson.model_dump_json()}")
        assert isinstance(lesson, Lesson)
        lesson.spoken_language = plan.spoken_language'''

new_agents = '''    spoken_rules = f"{spoken_generation_rules(plan.spoken_language)}\\n{CODE_TEACHING_RULES}"
    if plan.requires_code and (not has_code or empty_main):
        lesson = invoke_agent(CODE_AGENT, f"{spoken_rules}\\n{lesson.model_dump_json()}")
        assert isinstance(lesson, Lesson)
        lesson.spoken_language = plan.spoken_language
        lesson.requires_code = True
    has_highlights = any(
        getattr(scene, "highlight_ranges", None) for scene in lesson.scenes if scene.type == "code"
    )
    if plan.requires_code and not has_highlights:
        lesson = invoke_agent(VISUAL_AGENT, f"{spoken_rules}\\n{lesson.model_dump_json()}")
        assert isinstance(lesson, Lesson)
        lesson.spoken_language = plan.spoken_language
        lesson.requires_code = True'''

if old_agents not in ot:
    raise SystemExit("code/visual agent block missing")
ot = ot.replace(old_agents, new_agents, 1)

# _normalize_reel: allow concept for explain
old_norm = '''def _normalize_reel(lesson: Lesson) -> Lesson:
    from app.schemas.lesson import IntroScene, SummaryScene

    allowed = {"intro", "code", "execution", "terminal", "summary"}
    scenes = [scene for scene in lesson.scenes if scene.type in allowed]
    types = {scene.type for scene in scenes}
    locale = spoken_locale(lesson.spoken_language)
    if "intro" not in types:
        scenes.insert(
            0,
            IntroScene(
                id="scene_reel_hook",
                duration=6,
                narration=pick_reel_hook(lesson.spoken_language, lesson.topic, lesson.lesson_id),
            ),
        )
    if "summary" not in types:
        scenes.append(
            SummaryScene(
                id="scene_reel_end",
                duration=5,
                narration=locale.reel_end,
                takeaways=["Try it yourself", lesson.topic],
            ),
        )
    return lesson.model_copy(update={"format": LessonFormat.reel, "scenes": scenes})'''

new_norm = '''def _normalize_reel(lesson: Lesson) -> Lesson:
    from app.schemas.lesson import ConceptScene, IntroScene, SummaryScene

    explain = lesson.requires_code is False or (
        not any(scene.type == "code" for scene in lesson.scenes)
        and any(scene.type == "concept" for scene in lesson.scenes)
    )
    allowed = {"intro", "concept", "summary"} if explain else {"intro", "code", "execution", "terminal", "summary"}
    scenes = [scene for scene in lesson.scenes if scene.type in allowed]
    types = {scene.type for scene in scenes}
    locale = spoken_locale(lesson.spoken_language)
    if "intro" not in types:
        scenes.insert(
            0,
            IntroScene(
                id="scene_reel_hook",
                duration=6,
                narration=pick_reel_hook(lesson.spoken_language, lesson.topic, lesson.lesson_id),
            ),
        )
    if explain and "concept" not in types:
        scenes.insert(
            1,
            ConceptScene(
                id="scene_reel_concept",
                duration=14,
                narration=lesson.topic,
                bullets=[lesson.topic],
            ),
        )
    if "summary" not in types:
        scenes.append(
            SummaryScene(
                id="scene_reel_end",
                duration=5,
                narration=locale.reel_end,
                takeaways=["Save this", lesson.topic],
            ),
        )
    return lesson.model_copy(
        update={
            "format": LessonFormat.reel,
            "scenes": scenes,
            "requires_code": False if explain else lesson.requires_code,
        }
    )'''

if old_norm not in ot:
    raise SystemExit("_normalize_reel missing")
ot = ot.replace(old_norm, new_norm, 1)

orch.write_text(ot, encoding="utf-8")
print("orchestrator ok")
print("done")
