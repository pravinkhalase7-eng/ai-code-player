from __future__ import annotations

import logging
import re

from app.config import settings
from app.schemas.lesson import ChatReply, EvaluationResult, Lesson, LessonDraft, TutorPlan, lesson_from_draft
from app.services.gemini_client import generate_text, structured_generate

logger = logging.getLogger(__name__)

TUTOR_INSTRUCTION = """
You are the Tutor Agent for an AI Coding Tutor platform.
Understand the student's request, infer language and skill level, and decide what to teach.
Return JSON only matching TutorPlan.
Prefer the language the student selected in the request. Only default to Java if they did not name a language.
Teach the topic they asked for. Do not swap it for a different concept.
If they ask for Java Stream API, plan Stream pipelines (filter, map, collect), not a generic for-loop.
If they ask for a for loop, plan initialization, condition, increment, body, and execution order.
Never claim that code ran. Never invent terminal output.
""".strip()

PLANNER_INSTRUCTION = """
You are the Lesson Planner Agent.
Create a complete structured lesson for an interactive visual coding tutor that TEACHES THE REQUESTED TOPIC IN FULL.
The lesson MUST include scenes of types: intro, concept, code, execution, terminal, quiz, summary — in that order.

Hard rules:
- Teach the plan topic. Do not replace Stream API, recursion, classes, etc. with an unrelated for-loop.
- Intro narration: 4-6 spoken sentences that name the concept and what the student will be able to do.
- Concept narration: 6-10 spoken sentences that explain the idea completely, plus 4-6 bullets.
- Code scene MUST include a complete, runnable example of THIS topic.
  Java: public class Main in Main.java. Python: a complete main.py. JavaScript: a complete main.js.
  Never leave the program empty.
- Code narration walks through the example line by line (what each highlighted piece does).
- Include highlight_ranges that point at the important lines of that example.
- Include narration segments that sync those highlights.
- Execution and terminal scenes use the same example code.
- Quiz must test THIS topic (predict_output of the example when possible).
- Summary restates the concept and 3-5 takeaways.
- Do not invent execution output. Put expected_output as an empty list. The sandbox fills real stdout.
- narration must be spoken teaching, not UI copy. No one-sentence scenes except the quiz prompt.
- Durations: intro 18-28s, concept 28-45s, code 30-50s, execution 16-28s, terminal 12-20s, quiz 16-24s, summary 16-24s.
- language must match the tutor plan. Set filename to Main.java, main.py, or main.js to match.
- lesson_id should be a short slug.

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
""".strip()

CODE_INSTRUCTION = """
You are the Code Agent.
Given a lesson JSON, ensure every code and execution scene contains complete, compilable source for the lesson topic.
Use Main.java / public class Main for Java, main.py for Python, and main.js for JavaScript.
The example MUST demonstrate the requested topic (streams, loops, methods, etc.). Never leave main() empty.
Never replace a Stream/filter/map example with an unrelated for-loop unless the topic is loops.
Do not invent stdout. Keep expected_output empty.
Return the full Lesson JSON.
""".strip()

VISUAL_INSTRUCTION = """
You are the Visual Agent.
Given a lesson JSON, add highlight_ranges, narration segments, and visual callouts that match the actual example code.
Walk through the important lines in order.
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
If the student asks to change or run code, set should_execute true and provide the code.
Never invent execution output.
""".strip()

EVAL_INSTRUCTION = """
You are the Evaluation Agent.
Score the student's answer against the quiz.
status must be correct, partially_correct, or incorrect.
Identify misconceptions and recommend continue, reteach, harder, or practice.
mastery_delta is between -0.2 and 0.25.
""".strip()


class AgentSpec:
    def __init__(self, name: str, instruction: str, schema: type, temperature: float = 0.35) -> None:
        self.name = name
        self.instruction = instruction
        self.schema = schema
        self.temperature = temperature


TUTOR_AGENT = AgentSpec("tutor_agent", TUTOR_INSTRUCTION, TutorPlan, 0.3)
PLANNER_AGENT = AgentSpec("lesson_planner_agent", PLANNER_INSTRUCTION, LessonDraft, 0.25)
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
        return lesson_from_draft(result)
    return result


def plan_lesson(topic: str, language: str, level: str) -> TutorPlan:
    message = f"Topic: {topic}\nLanguage: {language}\nRequested level: {level}"
    plan = invoke_agent(TUTOR_AGENT, message)
    assert isinstance(plan, TutorPlan)
    if language:
        plan.language = language.lower()
    return plan


def generate_structured_lesson(plan: TutorPlan, lesson_id: str) -> Lesson:
    message = (
        f"Create the lesson. Teach THIS topic completely; do not substitute a different concept.\n"
        f"lesson_id={lesson_id}\n"
        f"title={plan.title}\n"
        f"topic={plan.topic}\n"
        f"language={plan.language}\n"
        f"level={plan.level.value}\n"
        f"objectives={plan.objectives}\n"
        f"concepts={plan.concepts}\n"
        f"greeting={plan.greeting}\n"
    )
    lesson = invoke_agent(PLANNER_AGENT, message)
    assert isinstance(lesson, Lesson)
    lesson.lesson_id = lesson_id
    lesson.language = plan.language
    lesson.level = plan.level
    lesson.topic = plan.topic
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
    if not has_code or empty_main:
        lesson = invoke_agent(CODE_AGENT, lesson.model_dump_json())
        assert isinstance(lesson, Lesson)
    has_highlights = any(
        getattr(scene, "highlight_ranges", None) for scene in lesson.scenes if scene.type == "code"
    )
    if not has_highlights:
        lesson = invoke_agent(VISUAL_AGENT, lesson.model_dump_json())
        assert isinstance(lesson, Lesson)
    has_quiz = any(scene.type == "quiz" for scene in lesson.scenes)
    if not has_quiz:
        lesson = invoke_agent(QUIZ_AGENT, lesson.model_dump_json())
        assert isinstance(lesson, Lesson)
    lesson.lesson_id = lesson_id
    return _fit_scene_durations(lesson)


def _fit_scene_durations(lesson: Lesson) -> Lesson:
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
