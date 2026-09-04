from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.lesson import Lesson, LessonDraft, QuizScene, lesson_from_draft
from app.services.gemini_client import extract_json
from app.services.tts.base import tts_hash
from app.services.visualizer import visualize_execution, visualize_java_for_loop

JAVA_FOR = """public class Main {
    public static void main(String[] args) {
        for (int i = 0; i < 5; i++) {
            System.out.println(i);
        }
    }
}
"""


def valid_lesson_payload() -> dict:
    return {
        "lesson_id": "java-for-loop",
        "title": "Java For Loop",
        "language": "java",
        "level": "beginner",
        "topic": "for loop",
        "objectives": [
            "Understand what a for loop does",
            "Understand initialization",
            "Understand condition",
            "Understand increment",
        ],
        "scenes": [
            {
                "id": "scene_1",
                "type": "intro",
                "duration": 8,
                "narration": "Absolutely! Let's learn the Java for loop step by step.",
            },
            {
                "id": "scene_2",
                "type": "concept",
                "duration": 12,
                "narration": "A for loop repeats work while a condition stays true.",
                "bullets": ["initialization", "condition", "increment", "body"],
            },
            {
                "id": "scene_3",
                "type": "code",
                "duration": 16,
                "language": "java",
                "code": JAVA_FOR,
                "narration": "First we create i and start it at zero.",
                "highlight_ranges": [
                    {"start_line": 4, "end_line": 4, "start_col": 13, "end_col": 24, "label": "initialization"}
                ],
                "segments": [
                    {"start": 0, "end": 3, "text": "Create i at zero.", "highlight": "initialization"}
                ],
            },
            {
                "id": "scene_4",
                "type": "execution",
                "duration": 18,
                "code": JAVA_FOR,
                "narration": "Watch i change on every iteration.",
                "expected_output": [],
                "iterations": [],
            },
            {
                "id": "scene_5",
                "type": "terminal",
                "duration": 8,
                "command": "java Main",
                "narration": "The sandbox prints each value of i.",
                "stdout": [],
            },
            {
                "id": "scene_6",
                "type": "quiz",
                "duration": 12,
                "kind": "predict_output",
                "question": "What will this print?",
                "options": ["0 1 2 3 4", "1 2 3 4 5", "0 1 2 3 4 5", "5 4 3 2 1"],
                "answer": 0,
                "narration": "Predict the output before we reveal it.",
            },
            {
                "id": "scene_7",
                "type": "summary",
                "duration": 8,
                "narration": "Initialization, condition, body, increment. Then repeat.",
                "takeaways": ["i starts at 0", "loop stops when i is 5"],
            },
        ],
    }


def test_lesson_schema_accepts_for_loop_lesson() -> None:
    lesson = Lesson.model_validate(valid_lesson_payload())
    assert lesson.language == "java"
    assert {scene.type for scene in lesson.scenes} >= {"intro", "code", "quiz"}


def test_lesson_schema_rejects_missing_scenes() -> None:
    payload = valid_lesson_payload()
    payload["scenes"] = [scene for scene in payload["scenes"] if scene["type"] != "quiz"]
    with pytest.raises(ValidationError):
        Lesson.model_validate(payload)


def test_quiz_rejects_out_of_range_answer() -> None:
    with pytest.raises(ValidationError):
        QuizScene(
            id="q1",
            duration=8,
            narration="Choose",
            question="What prints?",
            options=["a", "b"],
            answer=4,
        )


def test_gemini_json_fence_parsing() -> None:
    raw = """```json
    {"topic": "for loop", "language": "java"}
    ```"""
    assert extract_json(raw)["topic"] == "for loop"


def test_for_loop_visualizer_matches_stdout() -> None:
    steps = visualize_java_for_loop(JAVA_FOR, ["0", "1", "2", "3", "4"])
    printed = [step.output_line for step in steps if step.output_line is not None]
    assert printed == ["0", "1", "2", "3", "4"]
    assert any(step.stopped and step.condition_result is False for step in steps)
    assert steps[-1].variables[0].value == "5"


def test_python_and_js_visualizers() -> None:
    python_steps = visualize_execution("python", "for i in range(5):\n    print(i)\n", ["0", "1", "2", "3", "4"])
    assert [step.output_line for step in python_steps if step.output_line] == ["0", "1", "2", "3", "4"]
    js_steps = visualize_execution(
        "javascript",
        "for (let i = 0; i < 3; i++) {\n  console.log(i);\n}\n",
        ["0", "1", "2"],
    )
    assert [step.output_line for step in js_steps if step.output_line] == ["0", "1", "2"]


def test_lesson_draft_converts_to_strict_lesson() -> None:
    draft = LessonDraft.model_validate(valid_lesson_payload())
    lesson = lesson_from_draft(draft)
    assert isinstance(lesson, Lesson)
    assert {scene.type for scene in lesson.scenes} >= {"intro", "code", "quiz"}


def test_tts_hash_is_stable() -> None:
    first = tts_hash("hello", "af_bella", 1.0, "kokoro")
    second = tts_hash("hello", "af_bella", 1.0, "kokoro")
    other = tts_hash("hello", "af_bella", 1.1, "kokoro")
    assert first == second
    assert first != other
