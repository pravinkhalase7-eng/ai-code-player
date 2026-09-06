from __future__ import annotations

import logging

from app.db import SessionLocal
from app.services.jobs import set_job
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def run_job(job_id: str, kind: str) -> None:
    db = SessionLocal()
    try:
        set_job(db, job_id, status="running", progress=0.1)
        if kind == "lesson_generation":
            from app.services.lesson_service import build_lesson

            from app.models.orm import Job

            record = db.get(Job, job_id)
            if record is None:
                return
            payload = record.payload or {}
            set_job(db, job_id, progress=0.25)
            lesson = build_lesson(
                db,
                payload["lesson_id"],
                payload["topic"],
                payload.get("language", "java"),
                payload.get("level", "beginner"),
                payload.get("format", "lesson"),
                payload.get("spoken_language", "en"),
                payload.get("reel_seconds", 30),
                payload.get("requires_code"),
                payload.get("reel_mode"),
            )
            set_job(
                db,
                job_id,
                status="completed",
                progress=1.0,
                result={"lesson_id": lesson.lesson_id, "title": lesson.title},
            )
        elif kind == "code_execution":
            from app.models.orm import Job
            from app.services.lesson_service import record_execution

            record = db.get(Job, job_id)
            payload = record.payload if record else {}
            result = record_execution(
                db,
                payload.get("user_id"),
                payload.get("lesson_id"),
                payload.get("language", "java"),
                payload.get("code", ""),
            )
            set_job(db, job_id, status="completed", progress=1.0, result=result.model_dump())
        elif kind == "video_render":
            set_job(
                db,
                job_id,
                status="completed",
                progress=1.0,
                result={"message": "Use the frontend Remotion renderer to export MP4."},
            )
        else:
            set_job(db, job_id, status="failed", error=f"Unknown job kind {kind}")
    except Exception as exc:
        logger.exception("job %s failed", job_id)
        try:
            from app.models.orm import Job, LessonRow

            record = db.get(Job, job_id)
            if record and record.payload and record.payload.get("lesson_id"):
                lesson_row = db.get(LessonRow, record.payload["lesson_id"])
                if lesson_row:
                    lesson_row.status = "failed"
                    lesson_row.warnings = [str(exc)]
                    db.commit()
        except Exception:
            logger.exception("could not mark lesson failed")
        set_job(db, job_id, status="failed", error=str(exc))
    finally:
        db.close()


@celery_app.task(name="ai_coder.dispatch")
def dispatch(job_id: str, kind: str) -> None:
    run_job(job_id, kind)
