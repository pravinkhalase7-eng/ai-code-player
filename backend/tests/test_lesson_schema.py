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
    assert lesson.spoken_language == "en"
    assert {scene.type for scene in lesson.scenes} >= {"intro", "code", "quiz"}


def test_reel_schema_does_not_require_quiz() -> None:
    payload = {
        "lesson_id": "java-for-loop-reel",
        "title": "30s: Java For Loop",
        "language": "java",
        "level": "beginner",
        "format": "reel",
        "topic": "for loop",
        "objectives": ["Hook the concept", "Show a tiny example"],
        "scenes": [
            {"id": "hook", "type": "intro", "duration": 6, "narration": "Stop scrolling. Java for loops in 30 seconds."},
            {
                "id": "code",
                "type": "code",
                "duration": 12,
                "language": "java",
                "code": JAVA_FOR,
                "narration": "i starts at zero, runs while i is less than five, then i plus plus.",
            },
            {
                "id": "run",
                "type": "execution",
                "duration": 7,
                "code": JAVA_FOR,
                "narration": "Watch it print zero through four.",
            },
            {"id": "end", "type": "summary", "duration": 5, "narration": "Init, condition, increment. Save this.", "takeaways": ["i++ after the body"]},
        ],
    }
    lesson = Lesson.model_validate(payload)
    assert lesson.format.value == "reel"
    assert {scene.type for scene in lesson.scenes} >= {"intro", "code", "summary"}
    assert all(scene.type != "quiz" for scene in lesson.scenes)


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


def test_empty_execution_code_inherits_from_previous_scene() -> None:
    payload = {
        "lesson_id": "reel-empty-exec",
        "title": "30s: Java For Loop",
        "language": "java",
        "level": "beginner",
        "format": "reel",
        "topic": "for loop",
        "objectives": ["Hook the concept", "Show a tiny example"],
        "scenes": [
            {"id": "hook", "type": "intro", "duration": 6, "narration": "Stop scrolling. Java for loops in 30 seconds."},
            {
                "id": "code",
                "type": "code",
                "duration": 12,
                "language": "java",
                "code": JAVA_FOR,
                "narration": "i starts at zero, then i plus plus.",
            },
            {
                "id": "run",
                "type": "execution",
                "duration": 7,
                "code": "",
                "narration": "Watch it print zero through four.",
            },
            {
                "id": "end",
                "type": "summary",
                "duration": 5,
                "narration": "Init, condition, increment. Save this.",
                "takeaways": ["i++ after the body"],
            },
        ],
    }
    draft = LessonDraft.model_validate(payload)
    lesson = lesson_from_draft(draft)
    execution = next(scene for scene in lesson.scenes if scene.type == "execution")
    assert execution.code.strip() == JAVA_FOR.strip()

    strict = Lesson.model_validate(payload)
    execution = next(scene for scene in strict.scenes if scene.type == "execution")
    assert "for (int i = 0" in execution.code


def test_lesson_draft_converts_to_strict_lesson() -> None:
    draft = LessonDraft.model_validate(valid_lesson_payload())
    lesson = lesson_from_draft(draft)
    assert isinstance(lesson, Lesson)
    assert {scene.type for scene in lesson.scenes} >= {"intro", "code", "quiz"}


def test_reel_svg_thumbnail_includes_topic(tmp_path) -> None:
    from app.services.images.thumbnail import write_svg_poster, ensure_reel_thumbnail
    from app.config import settings

    dest = tmp_path / "poster.svg"
    write_svg_poster(dest, "Java for loop", "30s: Java For Loop", "java")
    body = dest.read_text()
    assert "Java For Loop" in body
    assert body.count("Java for loop") == 0
    assert "TECHSHALA" in body
    assert "BYTE" not in body

    original = settings.storage_path
    original_provider = settings.image_provider
    settings.storage_path = tmp_path
    settings.image_provider = "local"
    try:
        url = ensure_reel_thumbnail("les_thumb", "Java for loop", "30s: Java For Loop", "java")
        assert ".svg" in url
        assert (tmp_path / "images" / "thumb_les_thumb.svg").exists()
    finally:
        settings.storage_path = original
        settings.image_provider = original_provider


def test_reel_svg_thumbnail_formats_program(tmp_path) -> None:
    from app.services.images.thumbnail import write_svg_poster

    dest = tmp_path / "poster.svg"
    program = (
        "abstract class Car {\n"
        "    abstract void drive();\n"
        "}\n"
        "class SportsCar extends Car {\n"
        "    void drive() {}\n"
        "}\n"
    )
    write_svg_poster(dest, "Abstract class", "Abstract class", "java", program)
    body = dest.read_text()
    assert "abstract class Car" in body
    assert "xml:space=\"preserve\"" in body
    assert "\u00a0" in body
    assert "for (int i" not in body


def test_teaching_text_roundtrip_keeps_code() -> None:
    from app.agents.orchestrator import gather_teaching_texts, scatter_teaching_texts

    lesson = Lesson.model_validate(valid_lesson_payload())
    texts = gather_teaching_texts(lesson)
    translated = [f"HI:{item}" for item in texts]
    updated = scatter_teaching_texts(lesson, translated)
    assert updated.title.startswith("HI:")
    assert updated.scenes[0].narration.startswith("HI:")
    code_scene = next(scene for scene in updated.scenes if scene.type == "code")
    original = next(scene for scene in lesson.scenes if scene.type == "code")
    assert code_scene.code == original.code


def test_fit_reel_durations_total_about_30_seconds() -> None:
    from app.agents.orchestrator import _fit_reel_durations

    payload = valid_lesson_payload()
    payload["format"] = "reel"
    payload["reel_seconds"] = 30
    payload["scenes"] = [scene for scene in payload["scenes"] if scene["type"] != "quiz"]
    lesson = Lesson.model_validate(payload)
    fitted = _fit_reel_durations(lesson)
    total = sum(scene.duration for scene in fitted.scenes)
    assert 28.0 <= total <= 32.0


def test_fit_reel_durations_scales_to_60_and_90_seconds() -> None:
    from app.agents.orchestrator import _fit_reel_durations

    payload = valid_lesson_payload()
    payload["format"] = "reel"
    payload["scenes"] = [scene for scene in payload["scenes"] if scene["type"] != "quiz"]
    for seconds in (60, 90, 120):
        payload["reel_seconds"] = seconds
        lesson = Lesson.model_validate(payload)
        fitted = _fit_reel_durations(lesson)
        total = sum(scene.duration for scene in fitted.scenes)
        assert seconds - 3 <= total <= seconds + 3, (seconds, total)


def test_normalize_reel_seconds_snaps_to_choices() -> None:
    from app.schemas.lesson import normalize_reel_seconds

    assert normalize_reel_seconds(30) == 30
    assert normalize_reel_seconds(60) == 60
    assert normalize_reel_seconds(45) == 30
    assert normalize_reel_seconds(100) == 90
    assert normalize_reel_seconds("90") == 90
    assert normalize_reel_seconds(None) == 30


def test_tts_hash_is_stable() -> None:
    first = tts_hash("hello", "af_bella", 1.0, "kokoro")
    second = tts_hash("hello", "af_bella", 1.0, "kokoro")
    other = tts_hash("hello", "af_bella", 1.1, "kokoro")
    assert first == second
    assert first != other


def test_ensure_runnable_renames_java_class_to_main() -> None:
    from app.services.visualizer import ensure_runnable

    source = "public class Loop {\n    public static void main(String[] args) {\n        System.out.println(1);\n    }\n}\n"
    fixed = ensure_runnable("java", source)
    assert "public class Main" in fixed
    assert "public class Loop" not in fixed
    snippet = "System.out.println(2);"
    wrapped = ensure_runnable("java", snippet)
    assert "public class Main" in wrapped
    assert "System.out.println(2);" in wrapped
