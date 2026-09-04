from __future__ import annotations

import logging
import threading
from typing import Any

from sqlalchemy.orm import Session

from app.config import settings
from app.errors import AppError
from app.models.orm import (
    CodeExample,
    CodeExecution,
    LessonRow,
    LessonSceneRow,
    QuizQuestion,
    User,
)
from app.schemas.api import ExecuteResult, new_id
from app.schemas.lesson import (
    CodeScene,
    ExecutionScene,
    Lesson,
    QuizScene,
    TerminalScene,
)
from app.agents.orchestrator import generate_structured_lesson, plan_lesson
from app.db import SessionLocal
from app.services.execution.client import execute_in_sandbox
from app.services.jobs import create_job, enqueue, set_job
from app.services.tts.base import tts_hash
from app.services.tts.factory import audio_file_ready, cache_provider_key, synthesize_narration
from app.services.visualizer import extract_primary_code, run_command, source_filename, visualize_execution

logger = logging.getLogger(__name__)

_audio_refreshing: set[str] = set()
_audio_refresh_lock = threading.Lock()


def ensure_user(db: Session, user_id: str | None) -> str:
    uid = user_id or settings.default_user_id
    if not db.get(User, uid):
        db.add(User(id=uid, display_name="Student"))
        db.commit()
    return uid


def queue_lesson(
    db: Session,
    topic: str,
    language: str,
    level: str,
    user_id: str | None,
    format: str = "lesson",
) -> tuple[str, str]:
    uid = ensure_user(db, user_id)
    lesson_id = new_id("les_")
    fmt = "reel" if format == "reel" else "lesson"
    title = f"30s: {topic.title()}" if fmt == "reel" else topic.title()
    row = LessonRow(
        id=lesson_id,
        user_id=uid,
        title=title,
        language=language.lower(),
        level=level,
        topic=topic,
        status="queued",
        lesson_json={"format": fmt},
    )
    db.add(row)
    db.commit()
    job = create_job(
        db,
        "lesson_generation",
        {
            "lesson_id": lesson_id,
            "topic": topic,
            "language": language,
            "level": level,
            "format": fmt,
            "user_id": uid,
        },
    )
    enqueue(job.id, "lesson_generation")
    return lesson_id, job.id


def persist_lesson(db: Session, row: LessonRow, lesson: Lesson, warnings: list[str]) -> None:
    row.title = lesson.title
    row.language = lesson.language
    row.level = lesson.level.value
    row.topic = lesson.topic
    row.status = "ready"
    row.lesson_json = lesson.model_dump(mode="json")
    row.warnings = warnings
    db.query(LessonSceneRow).filter(LessonSceneRow.lesson_id == row.id).delete()
    db.query(QuizQuestion).filter(QuizQuestion.lesson_id == row.id).delete()
    for index, scene in enumerate(lesson.scenes):
        db.add(
            LessonSceneRow(
                lesson_id=row.id,
                scene_id=scene.id,
                type=scene.type,
                position=index,
                payload=scene.model_dump(mode="json"),
            )
        )
        if isinstance(scene, QuizScene):
            db.add(
                QuizQuestion(
                    lesson_id=row.id,
                    scene_id=scene.id,
                    kind=scene.kind.value,
                    payload=scene.model_dump(mode="json"),
                )
            )
    db.commit()


def _apply_execution(lesson: Lesson, result: ExecuteResult) -> Lesson:
    scenes = []
    for scene in lesson.scenes:
        if isinstance(scene, ExecutionScene):
            steps = visualize_execution(lesson.language, scene.code, result.stdout) or scene.iterations
            scenes.append(
                scene.model_copy(
                    update={
                        "expected_output": result.stdout,
                        "iterations": steps or scene.iterations,
                        "verified": result.success,
                        "narration": (
                            scene.narration
                            if result.success
                            else (
                                "Compilation Error. Let's read the compiler message together."
                                if result.compile_error
                                else scene.narration
                            )
                        ),
                    }
                )
            )
        elif isinstance(scene, TerminalScene):
            command = run_command(lesson.language)
            scenes.append(
                scene.model_copy(
                    update={
                        "command": command,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "success": result.success,
                        "verified": True,
                    }
                )
            )
        else:
            scenes.append(scene)
    return lesson.model_copy(update={"scenes": scenes})


def _stamp_language(lesson: Lesson) -> Lesson:
    filename = source_filename(lesson.language)
    scenes = []
    for scene in lesson.scenes:
        if isinstance(scene, CodeScene):
            scenes.append(scene.model_copy(update={"filename": filename, "language": lesson.language}))
        elif isinstance(scene, ExecutionScene):
            scenes.append(scene.model_copy(update={"language": lesson.language}))
        else:
            scenes.append(scene)
    return lesson.model_copy(update={"scenes": scenes})


def generate_lesson_assets(
    db: Session,
    lesson: Lesson,
    warnings: list[str],
    row: LessonRow | None = None,
) -> Lesson:
    updated_scenes = []
    remaining = list(lesson.scenes)
    for index, scene in enumerate(lesson.scenes):
        audio_url = scene.audio_url
        if scene.narration.strip():
            try:
                audio_url, used = synthesize_narration(db, scene.narration, provider_name="google")
                if used != "google":
                    warnings.append("Google Cloud narration was unavailable for a scene.")
                    audio_url = audio_url if used != "browser" else scene.audio_url
            except Exception as exc:
                logger.warning("Google Cloud TTS skipped for %s: %s", scene.id, exc)
                warnings.append("Google Cloud narration is unavailable for a scene.")
        updated_scenes.append(scene.model_copy(update={"audio_url": audio_url}))
        remaining = remaining[1:]
        if row is not None and index == 0:
            persist_lesson(db, row, lesson.model_copy(update={"scenes": updated_scenes + remaining}), warnings)
    return lesson.model_copy(update={"scenes": updated_scenes})


def lesson_needs_google_audio(lesson: Lesson) -> bool:
    voice = settings.tts_voice
    speed = settings.tts_speed
    for scene in lesson.scenes:
        expected = tts_hash(scene.narration, voice, speed, cache_provider_key("google"))
        url = scene.audio_url or ""
        if expected not in url or not audio_file_ready(url):
            return True
    return False


def schedule_google_audio(lesson_id: str) -> None:
    with _audio_refresh_lock:
        if lesson_id in _audio_refreshing:
            return
        _audio_refreshing.add(lesson_id)

    def _run() -> None:
        db = SessionLocal()
        try:
            row = db.get(LessonRow, lesson_id)
            if row is None or row.status != "ready" or not row.lesson_json:
                return
            lesson = Lesson.model_validate(row.lesson_json)
            warnings = list(row.warnings or [])
            updated = generate_lesson_assets(db, lesson, warnings, row=row)
            persist_lesson(db, row, updated, warnings)
        except Exception:
            logger.exception("Google Cloud audio refresh failed for %s", lesson_id)
        finally:
            db.close()
            with _audio_refresh_lock:
                _audio_refreshing.discard(lesson_id)

    threading.Thread(target=_run, daemon=True, name=f"google-tts-{lesson_id[-8:]}").start()


def build_lesson(db: Session, lesson_id: str, topic: str, language: str, level: str, format: str = "lesson") -> Lesson:
    row = db.get(LessonRow, lesson_id)
    if row is None:
        raise AppError(404, "Lesson not found", "That lesson does not exist.", "not_found")
    row.status = "running"
    db.commit()
    warnings: list[str] = []

    plan = plan_lesson(topic, language, level, format=format)
    lesson = generate_structured_lesson(plan, lesson_id)
    lesson = _stamp_language(lesson)

    language_name, code = extract_primary_code(lesson.model_dump(mode="json"))
    result: ExecuteResult | None = None
    if code.strip():
        try:
            result = execute_in_sandbox(language_name, code)
            db.add(
                CodeExecution(
                    user_id=row.user_id,
                    lesson_id=lesson_id,
                    language=language_name,
                    code=code,
                    success=result.success,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    execution_time_ms=result.execution_time_ms,
                    timed_out=result.timed_out,
                )
            )
            db.add(
                CodeExample(
                    lesson_id=lesson_id,
                    language=language_name,
                    code=code,
                    verified_output=result.stdout,
                )
            )
            db.commit()
            if result.timed_out:
                warnings.append("Execution stopped because the program exceeded the time limit.")
            elif result.compile_error:
                warnings.append("Compilation Error: the generated example did not compile. Showing the compiler output.")
            elif not result.success:
                warnings.append("The example ran with errors. The terminal shows the real sandbox output.")
            lesson = _apply_execution(lesson, result)
        except AppError as exc:
            warnings.append(exc.detail)
        except Exception as exc:
            logger.exception("sandbox failed during lesson build")
            warnings.append(str(exc))

    with _audio_refresh_lock:
        _audio_refreshing.add(lesson_id)
    try:
        try:
            lesson = generate_lesson_assets(db, lesson, warnings, row=row)
        except Exception:
            logger.exception("voice assets failed")
            warnings.append("Byte's voice is still being recorded. Playback starts when the audio files are ready.")
        persist_lesson(db, row, lesson, warnings)
        return lesson
    finally:
        with _audio_refresh_lock:
            _audio_refreshing.discard(lesson_id)


def record_execution(db: Session, user_id: str | None, lesson_id: str | None, language: str, code: str) -> ExecuteResult:
    result = execute_in_sandbox(language, code)
    db.add(
        CodeExecution(
            user_id=user_id,
            lesson_id=lesson_id,
            language=language,
            code=code,
            success=result.success,
            stdout=result.stdout,
            stderr=result.stderr,
            execution_time_ms=result.execution_time_ms,
            timed_out=result.timed_out,
        )
    )
    db.commit()
    steps = visualize_execution(language, code, result.stdout) if result.success else []
    return result.model_copy(update={"iterations": steps})


def list_recent_lessons(db: Session, user_id: str) -> list[dict[str, Any]]:
    rows = (
        db.query(LessonRow)
        .filter(LessonRow.user_id == user_id)
        .order_by(LessonRow.created_at.desc())
        .limit(12)
        .all()
    )
    results = []
    for row in rows:
        percent = 0.0
        scene_index = 0
        if row.progress:
            percent = row.progress[0].completion_percent
            scene_index = row.progress[0].scene_index
        results.append(
            {
                "lesson_id": row.id,
                "title": row.title,
                "language": row.language,
                "level": row.level,
                "status": row.status,
                "completion_percent": percent,
                "scene_index": scene_index,
                "topic": row.topic,
                "format": (row.lesson_json or {}).get("format") or "lesson",
            }
        )
    return results
