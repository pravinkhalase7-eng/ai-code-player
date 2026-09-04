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


def test_tts_cache_reuses_hash(tmp_path: Path, monkeypatch) -> None:
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
