from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("DATABASE_URL", f"sqlite:///{Path(__file__).parent / 'test.db'}")
os.environ.setdefault("GEMINI_API_KEY", "")

from uuid import uuid4

from fastapi.testclient import TestClient

from app.db import SessionLocal, init_db
from app.main import app
from app.models.orm import LessonRow, QuizQuestion, User
from app.services.progress_service import update_progress
from app.services.quiz_service import evaluate_quiz
from app.services.tts.base import tts_hash
from app.services.tts.factory import synthesize_narration


client = TestClient(app)


def setup_module() -> None:
    init_db()


def test_health_endpoint() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["gemini_model"]
    assert "missing_keys" in body


def test_create_lesson_queues_job() -> None:
    response = client.post(
        "/api/v1/tutor/lesson",
        json={"topic": "for loop", "language": "java", "level": "beginner"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["lesson_id"]
    assert body["status"] in {"queued", "running", "ready"}
    lesson = client.get(f"/api/v1/lesson/{body['lesson_id']}")
    assert lesson.status_code == 200


def test_create_lesson_accepts_hindi_spoken_language() -> None:
    response = client.post(
        "/api/v1/tutor/lesson",
        json={
            "topic": "for loop",
            "language": "java",
            "level": "beginner",
            "format": "reel",
            "spoken_language": "hindi",
        },
    )
    assert response.status_code == 200
    body = response.json()
    lesson = client.get(f"/api/v1/lesson/{body['lesson_id']}")
    assert lesson.status_code == 200
    assert lesson.json()["lesson"]["spoken_language"] == "hi"


def test_create_reel_queues_job() -> None:
    response = client.post(
        "/api/v1/tutor/lesson",
        json={"topic": "for loop", "language": "java", "level": "beginner", "format": "reel"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["lesson_id"]
    lesson = client.get(f"/api/v1/lesson/{body['lesson_id']}")
    assert lesson.status_code == 200
    listed = client.get("/api/v1/lessons")
    assert listed.status_code == 200
    match = next((item for item in listed.json()["lessons"] if item["lesson_id"] == body["lesson_id"]), None)
    assert match is not None
    assert match["format"] == "reel"


def test_quiz_and_progress(tmp_path: Path) -> None:
    db = SessionLocal()
    try:
        user = db.get(User, "demo-user")
        assert user is not None
        lesson_id = f"les_{uuid4().hex[:8]}"
        quiz_id = f"quiz_{uuid4().hex[:8]}"
        lesson = LessonRow(
            id=lesson_id,
            user_id=user.id,
            title="Java For Loop",
            language="java",
            level="beginner",
            topic="for loop",
            status="ready",
            lesson_json={"lesson_id": lesson_id},
        )
        db.add(lesson)
        db.add(
            QuizQuestion(
                id=quiz_id,
                lesson_id=lesson.id,
                scene_id="scene_6",
                kind="predict_output",
                payload={
                    "question": "What will this print?",
                    "options": ["0 1 2 3 4", "1 2 3 4 5"],
                    "answer": 0,
                    "explanation": "i runs 0 through 4.",
                },
            )
        )
        db.commit()
        evaluation, mastery = evaluate_quiz(db, quiz_id, user.id, 0, None, 0)
        assert evaluation.status == "correct"
        assert mastery is not None
        wrong, _ = evaluate_quiz(db, quiz_id, user.id, 1, None, 1)
        assert wrong.status == "incorrect"
        row = update_progress(
            db,
            user.id,
            lesson.id,
            current_scene="scene_6",
            scene_index=5,
            completion_percent=70,
            score=1,
            time_spent_ms=1200,
        )
        assert row.completion_percent == 70
        progress = client.get(f"/api/v1/lesson/{lesson.id}/progress")
        assert progress.status_code == 200
        assert progress.json()["completion_percent"] >= 70
    finally:
        db.close()


def test_save_reel_script_updates_narration(tmp_path: Path, monkeypatch) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "storage_path", tmp_path)
    monkeypatch.setattr(settings, "tts_provider", "browser")
    monkeypatch.setattr(settings, "tts_fallback_provider", "browser")
    monkeypatch.setattr(settings, "image_provider", "local")
    db = SessionLocal()
    try:
        user = db.get(User, "demo-user")
        assert user is not None
        lesson_id = f"les_{uuid4().hex[:8]}"
        payload = {
            "lesson_id": lesson_id,
            "title": "30s: Java For Loop",
            "language": "java",
            "level": "beginner",
            "format": "reel",
            "topic": "for loop",
            "objectives": ["Show a tiny example"],
            "scenes": [
                {"id": "hook", "type": "intro", "duration": 6, "narration": "Stop scrolling. Java for loops in 30 seconds."},
                {
                    "id": "code",
                    "type": "code",
                    "duration": 12,
                    "language": "java",
                    "code": "public class Main {\n    public static void main(String[] args) {\n        System.out.println(1);\n    }\n}\n",
                    "narration": "This prints one.",
                },
                {
                    "id": "run",
                    "type": "execution",
                    "duration": 7,
                    "code": "public class Main {\n    public static void main(String[] args) {\n        System.out.println(1);\n    }\n}\n",
                    "narration": "Watch the output.",
                },
                {"id": "end", "type": "summary", "duration": 5, "narration": "Save this.", "takeaways": ["println"]},
            ],
        }
        db.add(
            LessonRow(
                id=lesson_id,
                user_id=user.id,
                title=payload["title"],
                language="java",
                level="beginner",
                topic="for loop",
                status="ready",
                lesson_json=payload,
            )
        )
        db.commit()
    finally:
        db.close()
    edited = "This print starts at 1 and that is the whole trick."
    response = client.post(
        f"/api/v1/lesson/{lesson_id}/script",
        json={
            "code": payload["scenes"][1]["code"],
            "rewrite": False,
            "scenes": [
                {"id": "hook", "narration": edited},
                {"id": "code", "narration": "System.out.println(1) writes 1."},
                {"id": "run", "narration": "The run prints 1."},
                {"id": "end", "narration": "Remember println.", "takeaways": ["println"]},
            ],
        },
    )
    assert response.status_code == 200, response.text
    lesson = response.json()["lesson"]
    assert lesson["title"] == "Java For Loop"
    assert lesson["scenes"][0]["narration"] == edited
    assert "30" not in lesson["title"]


def test_rewrite_reel_script_returns_without_blocking_on_tts(tmp_path: Path, monkeypatch) -> None:
    from app.config import settings
    from app.schemas.lesson import ReelScriptDraft, ReelSceneScript
    import app.services.lesson_service as lesson_service

    monkeypatch.setattr(settings, "storage_path", tmp_path)
    monkeypatch.setattr(settings, "tts_provider", "browser")
    monkeypatch.setattr(settings, "tts_fallback_provider", "browser")
    monkeypatch.setattr(settings, "image_provider", "local")
    monkeypatch.setattr(
        lesson_service,
        "rewrite_reel_script",
        lambda lesson, code: ReelScriptDraft(
            scenes=[
                ReelSceneScript(id="hook", narration="This program starts a counter at zero."),
                ReelSceneScript(id="code", narration="System.out.println(1) prints 1."),
                ReelSceneScript(id="run", narration="The run prints 1 and stops."),
                ReelSceneScript(id="end", narration="Save this println trick.", takeaways=["println"]),
            ]
        ),
    )
    monkeypatch.setattr(lesson_service, "execute_in_sandbox", lambda language, code: type("R", (), {"stdout": ["1"], "stderr": "", "success": True, "compile_error": False})())
    monkeypatch.setattr(lesson_service, "schedule_google_audio", lambda lesson_id: None)
    monkeypatch.setattr(lesson_service, "schedule_reel_thumbnail", lambda lesson_id: None)
    db = SessionLocal()
    try:
        user = db.get(User, "demo-user")
        assert user is not None
        lesson_id = f"les_{uuid4().hex[:8]}"
        payload = {
            "lesson_id": lesson_id,
            "title": "Java For Loop",
            "language": "java",
            "level": "beginner",
            "format": "reel",
            "topic": "for loop",
            "objectives": ["Show a tiny example"],
            "scenes": [
                {"id": "hook", "type": "intro", "duration": 6, "narration": "Old hook."},
                {
                    "id": "code",
                    "type": "code",
                    "duration": 12,
                    "language": "java",
                    "code": "public class Main {\n    public static void main(String[] args) {\n        System.out.println(1);\n    }\n}\n",
                    "narration": "Old code line.",
                },
                {
                    "id": "run",
                    "type": "execution",
                    "duration": 7,
                    "code": "public class Main {\n    public static void main(String[] args) {\n        System.out.println(1);\n    }\n}\n",
                    "narration": "Old run.",
                },
                {"id": "end", "type": "summary", "duration": 5, "narration": "Old end.", "takeaways": ["println"]},
            ],
        }
        db.add(
            LessonRow(
                id=lesson_id,
                user_id=user.id,
                title=payload["title"],
                language="java",
                level="beginner",
                topic="for loop",
                status="ready",
                lesson_json=payload,
            )
        )
        db.commit()
    finally:
        db.close()
    response = client.post(
        f"/api/v1/lesson/{lesson_id}/script",
        json={
            "code": payload["scenes"][1]["code"],
            "rewrite": True,
            "scenes": [
                {"id": "hook", "narration": "Old hook."},
                {"id": "code", "narration": "Old code line."},
                {"id": "run", "narration": "Old run."},
                {"id": "end", "narration": "Old end."},
            ],
        },
    )
    assert response.status_code == 200, response.text
    lesson = response.json()["lesson"]
    assert "counter at zero" in lesson["scenes"][0]["narration"]
    from app.config import settings

    monkeypatch.setattr(settings, "storage_path", tmp_path)
    monkeypatch.setattr(settings, "tts_provider", "browser")
    monkeypatch.setattr(settings, "tts_fallback_provider", "browser")
    db = SessionLocal()
    try:
        path, provider = synthesize_narration(db, "Hello tutor")
        again, second_provider = synthesize_narration(db, "Hello tutor")
        assert path == again
        assert provider == "browser"
        assert second_provider == "browser"
        assert tts_hash("Hello tutor", settings.tts_voice, settings.tts_speed, "browser")
    finally:
        db.close()
