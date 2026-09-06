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
    LessonProgress,
    LessonRow,
    LessonSceneRow,
    QuizAttempt,
    QuizQuestion,
    User,
)
from app.schemas.api import ExecuteResult, new_id
from app.schemas.lesson import (
    CodeScene,
    ExecutionScene,
    Lesson,
    QuizScene,
    ReelSceneScript,
    TerminalScene,
    normalize_reel_seconds,
)
from app.agents.orchestrator import generate_structured_lesson, plan_lesson, rewrite_reel_script
from app.db import SessionLocal
from app.services.execution.client import execute_in_sandbox
from app.services.jobs import create_job, enqueue, set_job
from app.services.locale import hook_narration, spoken_locale, speech_text, strip_duration_copy, teachable_narration, tts_voice_for
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
    spoken_language: str = "en",
    reel_seconds: int = 30,
    requires_code: bool | None = None,
) -> tuple[str, str]:
    uid = ensure_user(db, user_id)
    lesson_id = new_id("les_")
    fmt = "reel" if format == "reel" else "lesson"
    spoken = spoken_locale(spoken_language).id
    seconds = normalize_reel_seconds(reel_seconds) if fmt == "reel" else 30
    title = topic.title()
    row = LessonRow(
        id=lesson_id,
        user_id=uid,
        title=title,
        language=language.lower(),
        level=level,
        topic=topic,
        status="queued",
        lesson_json={
            "format": fmt,
            "spoken_language": spoken,
            "reel_seconds": seconds,
            **({"requires_code": requires_code} if requires_code is not None else {}),
        },
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
            "spoken_language": spoken,
            "level": level,
            "format": fmt,
            "user_id": uid,
            "reel_seconds": seconds,
            **({"requires_code": requires_code} if requires_code is not None else {}),
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
                        "stderr": result.stderr or "",
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
    voice = tts_voice_for(lesson.spoken_language)
    for index, scene in enumerate(lesson.scenes):
        narration = _spoken_scene_text(lesson, scene)
        scene_patch: dict[str, Any] = {}
        if narration != scene.narration:
            scene_patch["narration"] = narration
            scene_patch["audio_url"] = None
        audio_url = scene.audio_url if not scene_patch else None
        if narration.strip():
            try:
                audio_url, used = synthesize_narration(
                    db, narration, provider_name="google", voice=voice
                )
                if used != "google":
                    warnings.append("Google Cloud narration was unavailable for a scene.")
                    audio_url = audio_url if used != "browser" else scene.audio_url
            except Exception as exc:
                logger.warning("Google Cloud TTS skipped for %s: %s", scene.id, exc)
                warnings.append("Google Cloud narration is unavailable for a scene.")
        scene_patch["audio_url"] = audio_url
        updated = scene.model_copy(update=scene_patch)
        updated_scenes.append(updated)
        remaining = remaining[1:]
        if row is not None and index == 0:
            persist_lesson(db, row, lesson.model_copy(update={"scenes": updated_scenes + remaining}), warnings)
    return lesson.model_copy(update={"scenes": updated_scenes})


def _spoken_scene_text(lesson: Lesson, scene: Any) -> str:
    narration = teachable_narration(scene.narration, lesson.spoken_language, scene.narration)
    if getattr(scene, "type", "") == "intro":
        return hook_narration(narration, lesson.spoken_language, lesson.topic, lesson.lesson_id)
    if getattr(scene, "type", "") == "concept":
        bullets = [str(b).strip() for b in (getattr(scene, "bullets", None) or []) if str(b).strip()]
        if bullets:
            joined = ". ".join(bullets)
            if narration and narration.strip() and narration.strip() not in joined:
                return f"{narration.strip()}. {joined}"
            return joined
    return narration


def lesson_needs_google_audio(lesson: Lesson) -> bool:
    voice = tts_voice_for(lesson.spoken_language)
    speed = settings.tts_speed
    for scene in lesson.scenes:
        expected = tts_hash(speech_text(_spoken_scene_text(lesson, scene)), voice, speed, cache_provider_key("google"))
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
            updated, warnings = _maybe_rerun_sandbox(updated, warnings)
            persist_lesson(db, row, updated, warnings)
        except Exception:
            logger.exception("Google Cloud audio refresh failed for %s", lesson_id)
        finally:
            db.close()
            with _audio_refresh_lock:
                _audio_refreshing.discard(lesson_id)

    threading.Thread(target=_run, daemon=True, name=f"google-tts-{lesson_id[-8:]}").start()


_thumbnail_refreshing: set[str] = set()
_thumbnail_lock = threading.Lock()


def upload_custom_thumbnail(
    db: Session,
    lesson_id: str,
    file_bytes: bytes,
    content_type: str | None = None,
) -> Lesson:
    row = db.get(LessonRow, lesson_id)
    if row is None or not row.lesson_json:
        raise AppError(404, "Lesson not found", "That lesson does not exist.", "not_found")
    if not file_bytes:
        raise AppError(400, "Empty upload", "Choose an image file to upload.", "bad_request")

    from app.services.images.thumbnail import images_dir

    ctype = (content_type or "").split(";")[0].strip().lower()
    ext_map = {
        "image/png": "png",
        "image/jpeg": "jpg",
        "image/jpg": "jpg",
        "image/webp": "webp",
    }
    ext = ext_map.get(ctype)
    folder = images_dir()
    dest_name = f"thumb_custom_{lesson_id}.png"
    dest = folder / dest_name

    try:
        from io import BytesIO

        from PIL import Image  # type: ignore

        image = Image.open(BytesIO(file_bytes))
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGBA" if "A" in image.getbands() else "RGB")
        image.save(dest, format="PNG")
        ext = "png"
        dest_name = dest.name
    except Exception:
        if ext is None:
            # sniff magic bytes
            if file_bytes[:8] == b"\x89PNG\r\n\x1a\n":
                ext = "png"
            elif file_bytes[:2] == b"\xff\xd8":
                ext = "jpg"
            elif file_bytes[:4] == b"RIFF" and file_bytes[8:12] == b"WEBP":
                ext = "webp"
            else:
                ext = "png"
        dest_name = f"thumb_custom_{lesson_id}.{ext}"
        dest = folder / dest_name
        dest.write_bytes(file_bytes)

    url = f"/images/{dest_name}?v=custom"
    lesson = Lesson.model_validate(row.lesson_json)
    updated = lesson.model_copy(update={"thumbnail_url": url, "thumbnail_custom": True})
    persist_lesson(db, row, updated, list(row.warnings or []))
    return updated


def refresh_reel_thumbnail(db: Session, lesson_id: str, *, force: bool = False) -> Lesson:
    row = db.get(LessonRow, lesson_id)
    if row is None or not row.lesson_json:
        raise AppError(404, "Lesson not found", "That lesson does not exist.", "not_found")
    lesson = Lesson.model_validate(row.lesson_json)
    if lesson.thumbnail_custom and not force:
        return lesson
    from app.services.images.thumbnail import ensure_reel_thumbnail

    _, program = extract_primary_code(lesson.model_dump(mode="json"))
    url = ensure_reel_thumbnail(
        lesson.lesson_id, lesson.topic, lesson.topic, lesson.language, program
    )
    updated = lesson.model_copy(update={"thumbnail_url": url, "thumbnail_custom": False})
    persist_lesson(db, row, updated, list(row.warnings or []))
    return updated


def schedule_reel_thumbnail(lesson_id: str) -> None:
    with _thumbnail_lock:
        if lesson_id in _thumbnail_refreshing:
            return
        _thumbnail_refreshing.add(lesson_id)

    def _run() -> None:
        db = SessionLocal()
        try:
            refresh_reel_thumbnail(db, lesson_id)
        except Exception:
            logger.exception("reel thumbnail refresh failed for %s", lesson_id)
        finally:
            db.close()
            with _thumbnail_lock:
                _thumbnail_refreshing.discard(lesson_id)

    threading.Thread(target=_run, daemon=True, name=f"thumb-{lesson_id[-8:]}").start()


_SANDBOX_RUNTIME_ERRORS = (
    "Unable to locate a Java Runtime",
    "javac is not installed",
    "java is not installed",
    "code runner is not reachable",
    "Code sandbox unavailable",
    "isolated code runner is not reachable",
)
_sandbox_refreshing: set[str] = set()
_sandbox_lock = threading.Lock()


def lesson_needs_sandbox_rerun(lesson: Lesson) -> bool:
    for scene in lesson.scenes:
        stderr = getattr(scene, "stderr", "") or ""
        if any(marker in stderr for marker in _SANDBOX_RUNTIME_ERRORS):
            return True
        if isinstance(scene, ExecutionScene):
            code = (getattr(scene, "code", "") or "").strip()
            has_output = bool(getattr(scene, "expected_output", None) or getattr(scene, "iterations", None))
            if code and not has_output:
                return True
    return False


def _maybe_rerun_sandbox(lesson: Lesson, warnings: list[str]) -> tuple[Lesson, list[str]]:
    if not lesson_needs_sandbox_rerun(lesson):
        return lesson, warnings
    _, program = extract_primary_code(lesson.model_dump(mode="json"))
    if not program.strip():
        return lesson, warnings
    result = execute_in_sandbox(lesson.language, program)
    updated = _apply_execution(lesson, result)
    cleaned = [item for item in warnings if "Compilation Error" not in item]
    if result.compile_error and not result.success:
        cleaned.append("Compilation Error: the generated example did not compile. Showing the compiler output.")
    return updated, cleaned


def schedule_sandbox_rerun(lesson_id: str) -> None:
    with _sandbox_lock:
        if lesson_id in _sandbox_refreshing:
            return
        _sandbox_refreshing.add(lesson_id)

    def _run() -> None:
        db = SessionLocal()
        try:
            row = db.get(LessonRow, lesson_id)
            if row is None or row.status != "ready" or not row.lesson_json:
                return
            lesson = Lesson.model_validate(row.lesson_json)
            warnings = list(row.warnings or [])
            updated, warnings = _maybe_rerun_sandbox(lesson, warnings)
            persist_lesson(db, row, updated, warnings)
        except Exception:
            logger.exception("sandbox rerun failed for %s", lesson_id)
        finally:
            db.close()
            with _sandbox_lock:
                _sandbox_refreshing.discard(lesson_id)

    threading.Thread(target=_run, daemon=True, name=f"sandbox-{lesson_id[-8:]}").start()


def build_lesson(
    db: Session,
    lesson_id: str,
    topic: str,
    language: str,
    level: str,
    format: str = "lesson",
    spoken_language: str = "en",
    reel_seconds: int = 30,
    requires_code: bool | None = None,
) -> Lesson:
    row = db.get(LessonRow, lesson_id)
    if row is None:
        raise AppError(404, "Lesson not found", "That lesson does not exist.", "not_found")
    row.status = "running"
    db.commit()
    warnings: list[str] = []

    if requires_code is None and isinstance(row.lesson_json, dict) and "requires_code" in row.lesson_json:
        requires_code = bool(row.lesson_json.get("requires_code"))
    plan = plan_lesson(
        topic,
        language,
        level,
        format=format,
        spoken_language=spoken_language,
        reel_seconds=reel_seconds,
        requires_code=requires_code,
    )
    lesson = generate_structured_lesson(plan, lesson_id)
    lesson = _stamp_language(lesson)

    language_name, code = extract_primary_code(lesson.model_dump(mode="json"))
    result: ExecuteResult | None = None
    if lesson.requires_code is False:
        code = ""
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
            lesson = _apply_execution(
                lesson,
                ExecuteResult(success=False, stdout=[], stderr=exc.detail, execution_time_ms=0),
            )
        except Exception as exc:
            logger.exception("sandbox failed during lesson build")
            warnings.append(str(exc))
            lesson = _apply_execution(
                lesson,
                ExecuteResult(success=False, stdout=[], stderr=str(exc), execution_time_ms=0),
            )

    if lesson.format.value == "reel" and not lesson.thumbnail_url:
        try:
            from app.services.images.thumbnail import ensure_reel_thumbnail

            lesson = lesson.model_copy(
                update={
                    "thumbnail_url": ensure_reel_thumbnail(
                        lesson.lesson_id,
                        lesson.topic,
                        lesson.topic,
                        lesson.language,
                        extract_primary_code(lesson.model_dump(mode="json"))[1],
                    )
                }
            )
        except Exception:
            logger.exception("reel thumbnail failed")
            warnings.append("Thumbnail is still generating.")

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
                "spoken_language": (row.lesson_json or {}).get("spoken_language") or "en",
                "level": row.level,
                "status": row.status,
                "completion_percent": percent,
                "scene_index": scene_index,
                "topic": row.topic,
                "format": (row.lesson_json or {}).get("format") or "lesson",
                "thumbnail_url": (row.lesson_json or {}).get("thumbnail_url"),
                "reel_seconds": (row.lesson_json or {}).get("reel_seconds") or 30,
            }
        )
    return results



def delete_lesson(db: Session, lesson_id: str) -> None:
    """Remove a lesson from Continue Learning (cascades related rows)."""
    row = db.get(LessonRow, lesson_id)
    if row is None:
        raise AppError(404, "Lesson not found", "That lesson does not exist.", "not_found")

    question_ids = [
        qid
        for (qid,) in db.query(QuizQuestion.id).filter(QuizQuestion.lesson_id == lesson_id).all()
    ]
    if question_ids:
        db.query(QuizAttempt).filter(QuizAttempt.question_id.in_(question_ids)).delete(synchronize_session=False)
    db.query(QuizQuestion).filter(QuizQuestion.lesson_id == lesson_id).delete(synchronize_session=False)
    db.query(LessonProgress).filter(LessonProgress.lesson_id == lesson_id).delete(synchronize_session=False)
    db.query(CodeExample).filter(CodeExample.lesson_id == lesson_id).delete(synchronize_session=False)
    db.query(CodeExecution).filter(CodeExecution.lesson_id == lesson_id).delete(synchronize_session=False)
    db.query(LessonSceneRow).filter(LessonSceneRow.lesson_id == lesson_id).delete(synchronize_session=False)
    db.delete(row)
    db.commit()

def update_reel_script(
    db: Session,
    lesson_id: str,
    *,
    code: str | None,
    scenes: list[ReelSceneScript],
    rewrite: bool,
) -> Lesson:
    row = db.get(LessonRow, lesson_id)
    if row is None or not row.lesson_json:
        raise AppError(404, "Lesson not found", "That lesson does not exist.", "not_found")
    try:
        return _update_reel_script(db, row, lesson_id, code=code, scenes=scenes, rewrite=rewrite)
    except AppError:
        raise
    except Exception:
        logger.exception("reel script update failed for %s", lesson_id)
        raise AppError(
            500,
            "Could not update the script",
            "Byte could not rewrite that script. Try again in a moment.",
            "script_failed",
        )


def _clip_narration(text: str, fallback: str) -> str:
    cleaned = (strip_duration_copy(text) or text or fallback).strip()
    return (cleaned or fallback)[:2000]


def _update_reel_script(
    db: Session,
    row: LessonRow,
    lesson_id: str,
    *,
    code: str | None,
    scenes: list[ReelSceneScript],
    rewrite: bool,
) -> Lesson:
    lesson = Lesson.model_validate(row.lesson_json)
    if lesson.requires_code is False:
        code = ""
    _, existing = extract_primary_code(lesson.model_dump(mode="json"))
    program = "" if lesson.requires_code is False else ((code or "").strip() or existing)
    updates = {item.id: item for item in scenes}
    if rewrite:
        if not program.strip():
            raise AppError(400, "Missing code", "Paste a program so Byte can rewrite the script.", "invalid")
        draft = rewrite_reel_script(lesson, program)
        updates = {item.id: item for item in draft.scenes}
    next_scenes = []
    for scene in lesson.scenes:
        patch: dict[str, Any] = {}
        item = updates.get(scene.id)
        if item:
            narration = teachable_narration(
                _clip_narration(item.narration, scene.narration),
                lesson.spoken_language,
                scene.narration,
            )
            if scene.type == "intro":
                narration = hook_narration(
                    narration, lesson.spoken_language, lesson.topic, lesson.lesson_id
                )
            if narration != scene.narration:
                patch["narration"] = narration
                patch["audio_url"] = None
                patch["segments"] = []
            if item.takeaways and getattr(scene, "takeaways", None) is not None:
                patch["takeaways"] = item.takeaways[:8]
        if program and scene.type in {"code", "execution", "terminal"}:
            patch["code"] = program
            if scene.type == "code":
                patch["highlight_ranges"] = []
                patch["segments"] = patch.get("segments", [])
        next_scenes.append(scene.model_copy(update=patch) if patch else scene)
    lesson = lesson.model_copy(
        update={
            "scenes": next_scenes,
            "title": strip_duration_copy(lesson.title) or lesson.topic,
        }
    )
    warnings = [item for item in list(row.warnings or []) if "Compilation Error" not in item]
    if program.strip():
        try:
            result = execute_in_sandbox(lesson.language, program)
            lesson = _apply_execution(lesson, result)
            if result.success:
                warnings = [item for item in warnings if "Compilation Error" not in item]
            elif result.compile_error:
                warnings.append("Compilation Error: the generated example did not compile. Showing the compiler output.")
        except Exception:
            logger.exception("sandbox run after script edit failed for %s", lesson_id)
    persist_lesson(db, row, lesson, warnings)
    schedule_google_audio(lesson_id)
    schedule_reel_thumbnail(lesson_id)
    return lesson
