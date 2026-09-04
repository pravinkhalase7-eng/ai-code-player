from __future__ import annotations

import logging
import re

from app.config import settings
from app.schemas.lesson import ChatReply, EvaluationResult, Lesson, LessonDraft, LessonFormat, ReelScriptDraft, TranslatedLines, TutorPlan, lesson_from_draft
from app.services.gemini_client import generate_text, structured_generate
from app.services.locale import needs_localization, spoken_generation_rules, spoken_locale, strip_duration_copy, uses_spoken_script

logger = logging.getLogger(__name__)

CODE_TEACHING_RULES = """
When code is on screen, teach THAT code — not a textbook definition.
For every highlighted line: quote the actual tokens, say what this example does, then say why that line exists.
Wrong: "A for loop repeats work while a condition stays true."
Right: "`int i = 0` starts the counter at 0. `i < 5` is the stop test — when i becomes 5 the loop ends. `i++` bumps i after the body so it is not infinite."
Never talk about 'the concept' in the abstract if the snippet is visible. Point at the line.
""".strip()

TUTOR_INSTRUCTION = """
You are the Tutor Agent for an AI Coding Tutor platform.
Understand the student's request, infer language and skill level, and decide what to teach.
Return JSON only matching TutorPlan.
Prefer the programming language the student selected in the request. Only default to Java if they did not name a language.
Speak and write teaching copy in the requested spoken language. Programming source stays in Java, Python, or JavaScript.
Teach the topic they asked for. Do not swap it for a different concept.
If they ask for Java Stream API, plan Stream pipelines (filter, map, collect), not a generic for-loop.
If they ask for a for loop, plan initialization, condition, increment, body, and execution order.
Never claim that code ran. Never invent terminal output.
""".strip()

PLANNER_INSTRUCTION = (
    CODE_TEACHING_RULES
    + """

You are the Lesson Planner Agent.
Create a complete structured lesson for an interactive visual coding tutor that TEACHES THE REQUESTED TOPIC IN FULL.
The lesson MUST include scenes of types: intro, concept, code, execution, terminal, quiz, summary — in that order.

Hard rules:
- FIRST: write every narration, title, quiz, bullet, and takeaway in the requested spoken_language. English copy is invalid when spoken_language is not en.
- Teach the plan topic. Do not replace Stream API, recursion, classes, etc. with an unrelated for-loop.
- Intro narration: 4-6 spoken sentences that name the concept and what the student will be able to do.
- Concept narration: 6-10 spoken sentences that explain the idea completely, plus 4-6 bullets.
- Code scene MUST include a complete, runnable example of THIS topic.
  Java: public class Main in Main.java. Python: a complete main.py. JavaScript: a complete main.js.
  Never leave the program empty.
- Code narration walks through THIS example line by line: quote the tokens, say what happens, say why the line is there.
  Do not give a generic definition of the topic while the editor is showing code.
- Include highlight_ranges that point at the important lines of that example.
- Include narration segments that sync those highlights. Each segment.text must mention the code it highlights.
- Execution and terminal scenes use the same example code.
- Quiz must test THIS topic (predict_output of the example when possible).
- Summary restates the concept and 3-5 takeaways.
- Do not invent execution output. Put expected_output as an empty list. The sandbox fills real stdout.
- narration must be spoken teaching, not UI copy. No one-sentence scenes except the quiz prompt.
- Durations: intro 18-28s, concept 28-45s, code 30-50s, execution 16-28s, terminal 12-20s, quiz 16-24s, summary 16-24s.
- language must match the tutor plan. Set filename to Main.java, main.py, or main.js to match.
- spoken_language must match the tutor plan. All narration, quiz text, bullets, takeaways, and titles use that spoken language.
- lesson_id should be a short slug.
- format must be "lesson".

Java for-loop example ONLY when the topic is loops:

public class Main {
    public static void main(String[] args) {
        for (int i = 0; i < 5; i++) {
            System.out.println(i);
        }
    }
}

Python for-loop example when the topic is a Python for loop:

for i in range(5):
    print(i)

JavaScript for-loop example when the topic is a JavaScript for loop:

for (let i = 0; i < 5; i++) {
    console.log(i);
}

Java Stream API example when the topic is streams:

import java.util.List;
import java.util.stream.Collectors;

public class Main {
    public static void main(String[] args) {
        List<Integer> numbers = List.of(1, 2, 3, 4, 5, 6);
        List<Integer> evensDoubled = numbers.stream()
            .filter(n -> n % 2 == 0)
            .map(n -> n * 2)
            .collect(Collectors.toList());
            System.out.println(evensDoubled);
    }
}
"""
).strip()

REEL_PLANNER_INSTRUCTION = (
    CODE_TEACHING_RULES
    + """

You are the Lesson Planner Agent for a catchy coding reel (TikTok / Instagram Reels / YouTube Shorts).
Create a fast, hooky visual short. Total spoken time across ALL scenes MUST be about 30 seconds (70-90 words total).

Required scenes IN THIS ORDER: intro, code, execution, summary.
Do NOT include concept or quiz scenes.

Hard rules:
- Intro (6-8s): Hook in the first sentence. Pattern interrupt. Name the concept. Energetic, spoken to camera.
- Code (10-12s): Tiny complete runnable example of THIS topic. 1-3 highlight_ranges.
  Highlight ONLY the teaching tokens (callback, Promise/.then, async/await). Never highlight braces, class/main wrappers, imports, or empty lines.
  Narrate the actual lines: quote the code, say what it does in this snippet, and why it's needed.
  Do not define the topic in the abstract. The one trick must be visible in the code.
- Execution (6-8s): Same example. Say what THIS output proves about those lines. expected_output must be an empty list.
- Summary (4-6s): One punchy takeaway. 2-3 short takeaways max. End by asking them to follow, save, or comment which option they would use.
- Spoken style: short sentences, no filler ("so", "basically", "in this video we will"). Catchy, not a lecture.
- Never say "30 seconds", "30s", or "in this short" in narration, titles, or on-screen copy. Just teach the code.
- Java: public class Main in Main.java. Python: complete main.py. JavaScript: complete main.js.
- Never invent stdout. Never claim the code already ran.
- format must be "reel".
- language must match the tutor plan. Set filename to Main.java, main.py, or main.js to match.
- spoken_language must match the tutor plan. All spoken lines, takeaways, and the title use that spoken language.
- lesson_id should be a short slug.
"""
).strip()

CODE_INSTRUCTION = """
You are the Code Agent.
Given a lesson JSON, ensure every code and execution scene contains complete, compilable source for the lesson topic.
Use Main.java / public class Main for Java, main.py for Python, and main.js for JavaScript.
The example MUST demonstrate the requested topic (streams, loops, methods, etc.). Never leave main() empty.
Never replace a Stream/filter/map example with an unrelated for-loop unless the topic is loops.
Do not invent stdout. Keep expected_output empty.
Do not rewrite narration into English. Keep the existing spoken language.
Return the full Lesson JSON.
""".strip()

VISUAL_INSTRUCTION = """
You are the Visual Agent.
Given a lesson JSON, add highlight_ranges, narration segments, and visual callouts that match the actual example code.
Walk through the important teaching lines in order.
Highlight ONLY lines that contain the idea being taught (callback, Promise, .then, async, await, etc.).
Never highlight braces, class Main / main() wrappers, imports, comments, or empty lines.
Each segment.text must quote or clearly name the highlighted code and say what it does and why.
Do not invent execution iterations or stdout. The backend visualizer will fill iterations from real output.
Return the full Lesson JSON.
""".strip()

QUIZ_INSTRUCTION = """
You are the Quiz Agent.
Ensure the lesson has at least one quiz scene.
Prefer predict_output for for-loops, with options such as 0 1 2 3 4.
You may add a fill_in_code quiz for i++.
Return the full Lesson JSON.
""".strip()

CHAT_INSTRUCTION = """
You are the Tutor Agent answering a follow-up during a live lesson.
Be concise, visual, and kind.
Reply in the lesson spoken_language. Keep code snippets in the programming language.
If the student asks to change or run code, set should_execute true and provide the code.
Never invent execution output.
""".strip()

EVAL_INSTRUCTION = """
You are the Evaluation Agent.
Score the student's answer against the quiz.
status must be correct, partially_correct, or incorrect.
Identify misconceptions and recommend continue, reteach, harder, or practice.
mastery_delta is between -0.2 and 0.25.
Write explanation in the lesson spoken_language when that field is present.
""".strip()


class AgentSpec:
    def __init__(self, name: str, instruction: str, schema: type, temperature: float = 0.35) -> None:
        self.name = name
        self.instruction = instruction
        self.schema = schema
        self.temperature = temperature


TUTOR_AGENT = AgentSpec("tutor_agent", TUTOR_INSTRUCTION, TutorPlan, 0.3)
PLANNER_AGENT = AgentSpec("lesson_planner_agent", PLANNER_INSTRUCTION, LessonDraft, 0.25)
REEL_PLANNER_AGENT = AgentSpec("reel_planner_agent", REEL_PLANNER_INSTRUCTION, LessonDraft, 0.35)
CODE_AGENT = AgentSpec("code_agent", CODE_INSTRUCTION, LessonDraft, 0.15)
VISUAL_AGENT = AgentSpec("visual_agent", VISUAL_INSTRUCTION, LessonDraft, 0.2)
QUIZ_AGENT = AgentSpec("quiz_agent", QUIZ_INSTRUCTION, LessonDraft, 0.2)
CHAT_AGENT = AgentSpec("tutor_chat_agent", CHAT_INSTRUCTION, ChatReply, 0.4)
EVAL_AGENT = AgentSpec("evaluation_agent", EVAL_INSTRUCTION, EvaluationResult, 0.1)


def _run_adk_agent(spec: AgentSpec, user_message: str):
    try:
        from google.adk.agents import LlmAgent
    except ImportError:
        try:
            from google.adk import Agent as LlmAgent  # type: ignore
        except ImportError:
            return None
    try:
        return LlmAgent(
            name=spec.name,
            model=settings.gemini_model,
            instruction=spec.instruction,
            output_schema=spec.schema,
        )
    except Exception as exc:  # pragma: no cover
        logger.info("ADK agent init skipped for %s: %s", spec.name, exc)
        return None


def build_adk_graph():
    agents = [
        _run_adk_agent(spec, "")
        for spec in (TUTOR_AGENT, PLANNER_AGENT, CODE_AGENT, VISUAL_AGENT, QUIZ_AGENT)
    ]
    defined = [agent for agent in agents if agent is not None]
    if len(defined) < 2:
        return None
    try:
        from google.adk.agents import SequentialAgent

        return SequentialAgent(name="lesson_pipeline", sub_agents=defined)
    except Exception:
        try:
            from google.adk import Workflow

            return Workflow(name="lesson_pipeline", edges=[("START", *defined)])
        except Exception as exc:
            logger.info("ADK graph unavailable: %s", exc)
            return None


def invoke_agent(spec: AgentSpec, user_message: str):
    _run_adk_agent(spec, user_message)
    result = structured_generate(
        spec.instruction,
        user_message,
        spec.schema,
        temperature=spec.temperature,
        label=spec.name,
    )
    if isinstance(result, LessonDraft):
        if spec.name == "reel_planner_agent":
            result.format = LessonFormat.reel
        return lesson_from_draft(result)
    return result


def plan_lesson(
    topic: str,
    language: str,
    level: str,
    format: str = "lesson",
    spoken_language: str = "en",
) -> TutorPlan:
    fmt = "reel" if format == "reel" else "lesson"
    locale = spoken_locale(spoken_language)
    message = (
        f"{spoken_generation_rules(locale.id)}\n"
        f"Topic: {topic}\nProgramming language: {language}\nRequested level: {level}\nFormat: {fmt}\n"
    )
    if fmt == "reel":
        message += "This is a 30-second catchy short/reel, not a full lesson. Keep the plan tight."
    plan = invoke_agent(TUTOR_AGENT, message)
    assert isinstance(plan, TutorPlan)
    if language:
        plan.language = language.lower()
    plan.spoken_language = locale.id
    plan.format = LessonFormat.reel if fmt == "reel" else LessonFormat.lesson
    return plan


def generate_structured_lesson(plan: TutorPlan, lesson_id: str) -> Lesson:
    plan = _localize_plan(plan)
    is_reel = plan.format == LessonFormat.reel
    message = (
        f"{spoken_generation_rules(plan.spoken_language)}\n"
        f"{CODE_TEACHING_RULES}\n"
        f"Create the {'30-second catchy reel' if is_reel else 'lesson'}. Teach THIS topic; do not substitute a different concept.\n"
        f"lesson_id={lesson_id}\n"
        f"title={plan.title}\n"
        f"topic={plan.topic}\n"
        f"language={plan.language}\n"
        f"spoken_language={plan.spoken_language}\n"
        f"level={plan.level.value}\n"
        f"format={plan.format.value}\n"
        f"objectives={plan.objectives}\n"
        f"concepts={plan.concepts}\n"
        f"greeting={plan.greeting}\n"
    )
    planner = REEL_PLANNER_AGENT if is_reel else PLANNER_AGENT
    lesson = invoke_agent(planner, message)
    assert isinstance(lesson, Lesson)
    lesson.lesson_id = lesson_id
    lesson.language = plan.language
    lesson.spoken_language = plan.spoken_language
    lesson.level = plan.level
    lesson.format = LessonFormat.reel if is_reel else LessonFormat.lesson
    lesson.topic = plan.topic
    if is_reel:
        title = plan.title or lesson.title
        lesson.title = strip_duration_copy(title) or plan.topic
        lesson = _normalize_reel(lesson)
    else:
        lesson.title = plan.title or lesson.title
    lesson = _fit_scene_durations(lesson)

    has_code = any(
        len(getattr(scene, "code", "") or "") > 40
        for scene in lesson.scenes
        if scene.type in {"code", "execution"}
    )
    empty_main = False
    for scene in lesson.scenes:
        code = getattr(scene, "code", "") or ""
        if scene.type in {"code", "execution"} and "public static void main" in code and "stream(" not in code.lower():
            if "for" not in plan.topic.lower() and "loop" not in plan.topic.lower() and (
                "stream" in plan.topic.lower() or "filter" in plan.topic.lower()
            ):
                empty_main = True
        if scene.type in {"code", "execution"} and re.search(r"main\s*\([^)]*\)\s*\{\s*\}", code):
            empty_main = True
    spoken_rules = f"{spoken_generation_rules(plan.spoken_language)}\n{CODE_TEACHING_RULES}"
    if not has_code or empty_main:
        lesson = invoke_agent(CODE_AGENT, f"{spoken_rules}\n{lesson.model_dump_json()}")
        assert isinstance(lesson, Lesson)
        lesson.spoken_language = plan.spoken_language
    has_highlights = any(
        getattr(scene, "highlight_ranges", None) for scene in lesson.scenes if scene.type == "code"
    )
    if not has_highlights:
        lesson = invoke_agent(VISUAL_AGENT, f"{spoken_rules}\n{lesson.model_dump_json()}")
        assert isinstance(lesson, Lesson)
        lesson.spoken_language = plan.spoken_language
    has_quiz = any(scene.type == "quiz" for scene in lesson.scenes)
    if not has_quiz and lesson.format != LessonFormat.reel:
        lesson = invoke_agent(QUIZ_AGENT, f"{spoken_rules}\n{lesson.model_dump_json()}")
        assert isinstance(lesson, Lesson)
        lesson.spoken_language = plan.spoken_language
    lesson.lesson_id = lesson_id
    lesson.format = plan.format
    lesson.spoken_language = plan.spoken_language
    if lesson.format == LessonFormat.reel:
        lesson = _normalize_reel(lesson)
    lesson = _localize_lesson(lesson)
    return _fit_scene_durations(lesson)


def _normalize_reel(lesson: Lesson) -> Lesson:
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
                narration=locale.reel_hook.format(topic=lesson.topic),
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
    return lesson.model_copy(update={"format": LessonFormat.reel, "scenes": scenes})


def gather_teaching_texts(lesson: Lesson) -> list[str]:
    texts = [lesson.title, *list(lesson.objectives)]
    for scene in lesson.scenes:
        texts.append(scene.narration)
        texts.extend(segment.text for segment in scene.segments)
        texts.extend(list(getattr(scene, "bullets", None) or []))
        texts.extend(list(getattr(scene, "takeaways", None) or []))
        question = getattr(scene, "question", None)
        if question:
            texts.append(str(question))
        texts.extend(list(getattr(scene, "options", None) or []))
        explanation = getattr(scene, "explanation", None)
        if explanation:
            texts.append(str(explanation))
    return texts


def scatter_teaching_texts(lesson: Lesson, texts: list[str]) -> Lesson:
    expected = gather_teaching_texts(lesson)
    if len(texts) != len(expected):
        raise ValueError(f"translated line count {len(texts)} != {len(expected)}")
    cursor = iter(texts)
    title = next(cursor)[:160]
    objectives = [next(cursor)[:200] for _ in lesson.objectives]
    scenes = []
    for scene in lesson.scenes:
        updates: dict[str, object] = {
            "narration": next(cursor)[:2000],
            "segments": [segment.model_copy(update={"text": next(cursor)}) for segment in scene.segments],
        }
        bullets = getattr(scene, "bullets", None)
        if bullets:
            updates["bullets"] = [next(cursor) for _ in bullets]
        takeaways = getattr(scene, "takeaways", None)
        if takeaways:
            updates["takeaways"] = [next(cursor) for _ in takeaways]
        question = getattr(scene, "question", None)
        if question:
            updates["question"] = next(cursor)
        options = getattr(scene, "options", None)
        if options:
            updates["options"] = [next(cursor) for _ in options]
        explanation = getattr(scene, "explanation", None)
        if explanation:
            updates["explanation"] = next(cursor)
        scenes.append(scene.model_copy(update=updates))
    return lesson.model_copy(update={"title": title, "objectives": objectives, "scenes": scenes})


def _translate_lines(lines: list[str], spoken_language: str) -> list[str]:
    locale = spoken_locale(spoken_language)
    numbered = "\n".join(f"{index}. {line}" for index, line in enumerate(lines))
    instruction = (
        f"Translate every numbered line into {locale.english_name} using {locale.native_label} script.\n"
        f"Return JSON {{\"lines\": [...]}} with EXACTLY {len(lines)} strings in the same order.\n"
        "Keep programming tokens (for, if, i++, System.out.println, class names) in English.\n"
        "Do not add or drop lines. Do not answer in English prose."
    )
    last_error: Exception | None = None
    for attempt in range(2):
        try:
            drafted = structured_generate(
                instruction if attempt == 0 else instruction + "\nPrevious output had the wrong line count or was still English.",
                numbered,
                TranslatedLines,
                temperature=0.1,
                label="localize_lines",
            )
            assert isinstance(drafted, TranslatedLines)
            if len(drafted.lines) != len(lines):
                last_error = ValueError(f"count {len(drafted.lines)}")
                continue
            return [item if item.strip() else original for item, original in zip(drafted.lines, lines, strict=True)]
        except Exception as exc:
            last_error = exc
            logger.warning("line translation attempt %s failed: %s", attempt + 1, exc)
    raise last_error or RuntimeError("line translation failed")


def _localize_plan(plan: TutorPlan) -> TutorPlan:
    locale = spoken_locale(plan.spoken_language)
    if locale.id == "en":
        return plan
    blob = " ".join([plan.title, plan.greeting, *plan.objectives, *plan.concepts])
    if uses_spoken_script(blob, locale.id):
        return plan
    try:
        lines = [plan.title, plan.greeting, *plan.objectives, *plan.concepts]
        translated = _translate_lines(lines, locale.id)
        title, greeting, *rest = translated
        objectives = rest[: len(plan.objectives)]
        concepts = rest[len(plan.objectives) :]
        return plan.model_copy(
            update={
                "title": title[:160],
                "greeting": greeting[:400],
                "objectives": [item[:200] for item in objectives],
                "concepts": [item[:120] for item in concepts],
            }
        )
    except Exception:
        logger.exception("plan localization failed")
        return plan


def _localize_lesson(lesson: Lesson) -> Lesson:
    locale = spoken_locale(lesson.spoken_language)
    if locale.id == "en" or not needs_localization(lesson, locale.id):
        return lesson
    try:
        texts = gather_teaching_texts(lesson)
        translated = _translate_lines(texts, locale.id)
        localized = scatter_teaching_texts(lesson, translated)
        localized.spoken_language = locale.id
        return localized
    except Exception:
        logger.exception("localization failed for %s", lesson.lesson_id)
        return lesson


def _fit_scene_durations(lesson: Lesson) -> Lesson:
    if lesson.format == LessonFormat.reel:
        return _fit_reel_durations(lesson)
    updated = []
    for scene in lesson.scenes:
        words = max(1, len(scene.narration.split()))
        spoken = min(55.0, max(12.0, words / 2.3 + 2.0))
        if scene.type == "code":
            spoken = max(spoken, 28.0)
        elif scene.type == "concept":
            spoken = max(spoken, 24.0)
        updated.append(scene.model_copy(update={"duration": round(spoken, 1)}))
    return lesson.model_copy(update={"scenes": updated})


def _fit_reel_durations(lesson: Lesson) -> Lesson:
    target = 30.0
    caps = {
        "intro": (5.5, 8.0),
        "code": (9.0, 12.0),
        "execution": (5.5, 8.0),
        "terminal": (4.0, 6.0),
        "summary": (4.0, 6.0),
    }
    raw: list[float] = []
    for scene in lesson.scenes:
        words = max(1, len(scene.narration.split()))
        spoken = min(12.0, max(4.0, words / 2.6 + 0.6))
        low, high = caps.get(scene.type, (4.0, 8.0))
        raw.append(min(high, max(low, spoken)))
    total = sum(raw) or 1.0
    scale = target / total
    updated = []
    for scene, spoken in zip(lesson.scenes, raw, strict=True):
        duration = round(max(3.5, min(12.0, spoken * scale)), 1)
        updated.append(scene.model_copy(update={"duration": duration}))
    return lesson.model_copy(update={"scenes": updated})


def chat_reply(lesson_json: str, message: str) -> ChatReply:
    payload = f"Lesson JSON:\n{lesson_json}\n\nStudent: {message}"
    reply = invoke_agent(CHAT_AGENT, payload)
    assert isinstance(reply, ChatReply)
    return reply


def evaluate_answer(quiz_json: str, answer: str) -> EvaluationResult:
    payload = f"Quiz:\n{quiz_json}\n\nStudent answer:\n{answer}"
    result = invoke_agent(EVAL_AGENT, payload)
    assert isinstance(result, EvaluationResult)
    return result


def friendly_fallback_reply(message: str) -> str:
    try:
        return generate_text(
            "You are a friendly coding tutor. Answer in 4 sentences or fewer.",
            message,
        )
    except Exception:
        return "I ran into a problem answering that. Try asking about a specific line of the code."


def rewrite_reel_script(lesson: Lesson, code: str) -> ReelScriptDraft:
    spoken = spoken_generation_rules(lesson.spoken_language)
    ids = [scene.id for scene in lesson.scenes]
    message = (
        f"{spoken}\n{CODE_TEACHING_RULES}\n"
        f"Rewrite the spoken script so it teaches THIS program, not a generic definition.\n"
        f"Keep the same scene ids in this order: {ids}\n"
        f"topic={lesson.topic}\n"
        f"language={lesson.language}\n"
        f"spoken_language={lesson.spoken_language}\n"
        f"Program:\n{code}\n"
        "Never say 30 seconds, 30s, or 'this short'. Quote real tokens. Say what this code does and why.\n"
        "Intro: hook the trick in this program. Code: walk the important lines. "
        "Execution: what the output proves. Summary: one takeaway plus a follow/save/comment ask."
    )
    draft = structured_generate(
        "You rewrite coding-reel scripts. Return JSON only matching ReelScriptDraft.",
        message,
        ReelScriptDraft,
        temperature=0.4,
        label="reel_script_rewrite",
    )
    assert isinstance(draft, ReelScriptDraft)
    by_id = {item.id: item for item in draft.scenes}
    ordered = []
    for scene in lesson.scenes:
        item = by_id.get(scene.id)
        if item is None:
            item = next((row for row in draft.scenes if row.id not in {s.id for s in ordered}), None)
        if item is None:
            continue
        ordered.append(
            item.model_copy(
                update={
                    "id": scene.id,
                    "narration": strip_duration_copy(item.narration) or item.narration,
                }
            )
        )
    if not ordered:
        return draft
    return ReelScriptDraft(scenes=ordered)
    try:
        return generate_text(
            "You are a friendly coding tutor. Answer in 4 sentences or fewer.",
            message,
        )
    except Exception:
        return "I ran into a problem answering that. Try asking about a specific line of the code."
