from __future__ import annotations

import re
import wave
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
    reel_mode: str | None = None,
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
            **({"reel_mode": reel_mode} if reel_mode else {}),
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
            **({"reel_mode": reel_mode} if reel_mode else {}),
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
        # Sanitize persisted narration if an older TTS pass appended bullet lists.
        bullets = [str(b).strip() for b in (getattr(scene, "bullets", None) or []) if str(b).strip()]
        cleaned_narration = _strip_appended_bullet_list(scene.narration or "", bullets)
        scene_patch: dict[str, Any] = {}
        if cleaned_narration != (scene.narration or "").strip():
            scene_patch["narration"] = cleaned_narration
            scene = scene.model_copy(update={"narration": cleaned_narration})
            scene_patch["audio_url"] = None
        spoken = _spoken_scene_text(lesson, scene)
        # Speak `spoken` but do NOT write TTS enrichment back into narration.
        audio_url = None if "audio_url" in scene_patch else scene.audio_url
        if spoken.strip():
            try:
                audio_url, used = synthesize_narration(
                    db, spoken, provider_name="google", voice=voice
                )
                if used != "google":
                    warnings.append("Google Cloud narration was unavailable for a scene.")
                    audio_url = audio_url if used != "browser" else scene.audio_url
            except Exception as exc:
                logger.warning("Google Cloud TTS skipped for %s: %s", scene.id, exc)
                warnings.append("Google Cloud narration is unavailable for a scene.")
        scene_patch["audio_url"] = audio_url
        updated = scene.model_copy(update=scene_patch)
        updated = _align_scene_to_audio(updated, audio_url)
        updated_scenes.append(updated)
        remaining = remaining[1:]
        if row is not None and index == 0:
            persist_lesson(db, row, lesson.model_copy(update={"scenes": updated_scenes + remaining}), warnings)
    return lesson.model_copy(update={"scenes": updated_scenes})


def _strip_appended_bullet_list(narration: str, bullets: list[str]) -> str:
    """Remove trailing on-screen bullet dumps that TTS enrichment used to persist."""
    text = (narration or "").strip()
    if not text:
        return text
    # Cut at first English numbered list dump like "1. Heap Allocation"
    m = re.search(r"([।.])\s*1\.\s+[A-Za-z]", text)
    if m and m.start() > 40:
        return text[: m.start() + 1].strip()
    m = re.search(r"\s1\.\s+[A-Za-z].*2\.\s+[A-Za-z]", text)
    if m and m.start() > 40:
        return text[: m.start()].rstrip(" .।") + ("।" if "।" in text[: m.start()] else ".")
    if bullets:
        first = bullets[0]
        idx = text.find(first)
        if idx > 40 and re.search(r"\d+\.\s*" + re.escape(first), text[idx - 5 : idx + len(first) + 5]):
            prev = max(text.rfind("।", 0, idx), text.rfind(".", 0, idx))
            if prev > 20:
                return text[: prev + 1].strip()
    return text


def _spoken_scene_text(lesson: Lesson, scene: Any) -> str:
    bullets = [str(b).strip() for b in (getattr(scene, "bullets", None) or []) if str(b).strip()]
    cleaned = _strip_appended_bullet_list(scene.narration or "", bullets)
    narration = teachable_narration(cleaned, lesson.spoken_language, cleaned)
    if getattr(scene, "type", "") == "intro":
        return hook_narration(narration, lesson.spoken_language, lesson.topic, lesson.lesson_id)
    # Concept/explainer: on-screen bullets/diagram titles stay visual-only.
    # Never append them into TTS — that used to persist and multiply on each audio refresh.
    return narration



def _audio_duration_seconds(audio_url: str | None) -> float | None:
    """Read WAV length for a stored /audio/... url."""
    if not audio_url:
        return None
    from pathlib import Path as _Path
    name = _Path(str(audio_url)).name
    for base in (
        _Path(settings.storage_path) / "audio",
        _Path(__file__).resolve().parents[2] / "storage" / "audio",
        _Path(__file__).resolve().parents[3] / "storage" / "audio",
    ):
        if base is None:
            continue
        path = base / name
        if not path.is_file():
            continue
        try:
            with wave.open(str(path), "rb") as handle:
                rate = float(handle.getframerate() or 1)
                frames = float(handle.getnframes() or 0)
                if rate > 0 and frames > 0:
                    return frames / rate
        except Exception:
            return None
    return None


def _align_scene_to_audio(scene: Any, audio_url: str | None) -> Any:
    """Snap scene.duration + segments to the real TTS WAV so board/cues match speech."""
    dur = _audio_duration_seconds(audio_url)
    if not dur or dur < 0.4:
        return scene
    dur = round(float(dur), 2)
    segments = list(getattr(scene, "segments", None) or [])
    if not segments:
        return scene.model_copy(update={"duration": dur, "audio_url": audio_url or scene.audio_url})
    last = max(float(getattr(s, "end", 0) or 0) for s in segments) or 0.0
    if last <= 0.05:
        return scene.model_copy(update={"duration": dur, "audio_url": audio_url or scene.audio_url})
    scale = dur / last
    updated = []
    for seg in segments:
        start = round(float(seg.start or 0) * scale, 2)
        end = round(float(seg.end or 0) * scale, 2)
        updated.append(seg.model_copy(update={"start": start, "end": max(start + 0.05, end)}))
    if updated:
        updated[-1] = updated[-1].model_copy(update={"end": dur})
    return scene.model_copy(
        update={"duration": dur, "segments": updated, "audio_url": audio_url or scene.audio_url}
    )

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
        lesson.lesson_id,
        lesson.topic,
        lesson.topic,
        lesson.language,
        program,
        reel_mode=getattr(lesson, "reel_mode", None),
        spoken_language=getattr(lesson, "spoken_language", None),
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
    reel_mode: str | None = None,
) -> Lesson:
    row = db.get(LessonRow, lesson_id)
    if row is None:
        raise AppError(404, "Lesson not found", "That lesson does not exist.", "not_found")
    row.status = "running"
    db.commit()
    warnings: list[str] = []

    if requires_code is None and isinstance(row.lesson_json, dict) and "requires_code" in row.lesson_json:
        requires_code = bool(row.lesson_json.get("requires_code"))
    if not reel_mode and isinstance(row.lesson_json, dict):
        reel_mode = row.lesson_json.get("reel_mode")
    plan = plan_lesson(
        topic,
        language,
        level,
        format=format,
        spoken_language=spoken_language,
        reel_seconds=reel_seconds,
        requires_code=requires_code,
        reel_mode=reel_mode,
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
                        reel_mode=getattr(lesson, "reel_mode", None),
                        spoken_language=getattr(lesson, "spoken_language", None),
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
                "reel_mode": (row.lesson_json or {}).get("reel_mode"),
                "requires_code": (row.lesson_json or {}).get("requires_code"),
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


def delete_all_lessons(db: Session) -> dict[str, int]:
    """Remove every lesson and related rows; clear generated audio files."""
    from pathlib import Path as _Path

    lesson_ids = [lid for (lid,) in db.query(LessonRow.id).all()]
    count = len(lesson_ids)
    if lesson_ids:
        question_ids = [
            qid
            for (qid,) in db.query(QuizQuestion.id).filter(QuizQuestion.lesson_id.in_(lesson_ids)).all()
        ]
        if question_ids:
            db.query(QuizAttempt).filter(QuizAttempt.question_id.in_(question_ids)).delete(synchronize_session=False)
        db.query(QuizQuestion).filter(QuizQuestion.lesson_id.in_(lesson_ids)).delete(synchronize_session=False)
        db.query(LessonProgress).filter(LessonProgress.lesson_id.in_(lesson_ids)).delete(synchronize_session=False)
        db.query(CodeExample).filter(CodeExample.lesson_id.in_(lesson_ids)).delete(synchronize_session=False)
        db.query(CodeExecution).filter(CodeExecution.lesson_id.in_(lesson_ids)).delete(synchronize_session=False)
        db.query(LessonSceneRow).filter(LessonSceneRow.lesson_id.in_(lesson_ids)).delete(synchronize_session=False)
        db.query(LessonRow).delete(synchronize_session=False)
        db.commit()

    audio_removed = 0
    audio_dir = _Path(__file__).resolve().parents[2] / "storage" / "audio"
    if audio_dir.is_dir():
        for path in audio_dir.rglob("*"):
            if path.is_file():
                try:
                    path.unlink()
                    audio_removed += 1
                except OSError:
                    pass

    return {"lessons": count, "audio_files": audio_removed}


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
