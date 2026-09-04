from __future__ import annotations

import logging
import threading
from typing import Any

from sqlalchemy.orm import Session

from app.config import settings
from app.models.orm import Job, LessonRow
from app.schemas.api import new_id

logger = logging.getLogger(__name__)

_active_jobs: set[str] = set()
_active_lock = threading.Lock()


def create_job(db: Session, kind: str, payload: dict[str, Any]) -> Job:
    job = Job(id=new_id("job_"), kind=kind, status="queued", payload=payload)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def set_job(db: Session, job_id: str, **fields: Any) -> Job | None:
    job = db.get(Job, job_id)
    if not job:
        return None
    for key, value in fields.items():
        setattr(job, key, value)
    db.commit()
    db.refresh(job)
    return job


def _redis_ready() -> bool:
    try:
        import redis

        client = redis.Redis.from_url(settings.redis_url, socket_connect_timeout=0.4)
        return bool(client.ping())
    except Exception:
        return False


def enqueue(job_id: str, kind: str) -> None:
    if settings.use_celery and not settings.celery_eager and _redis_ready():
        try:
            from app.workers.tasks import dispatch

            dispatch.delay(job_id, kind)
            return
        except Exception as exc:
            logger.info("Celery dispatch failed (%s); using a worker thread", exc)

    with _active_lock:
        if job_id in _active_jobs:
            return
        _active_jobs.add(job_id)

    from app.workers.tasks import run_job

    def _run() -> None:
        try:
            run_job(job_id, kind)
        finally:
            with _active_lock:
                _active_jobs.discard(job_id)

    thread = threading.Thread(target=_run, args=(), daemon=True, name=f"job-{kind}")
    thread.start()


def resume_lesson_job(db: Session, lesson_id: str) -> None:
    row = db.get(LessonRow, lesson_id)
    if row is None or row.status not in {"queued", "running"}:
        return

    match: Job | None = None
    jobs = (
        db.query(Job)
        .filter(Job.kind == "lesson_generation")
        .order_by(Job.created_at.desc())
        .limit(80)
        .all()
    )
    for job in jobs:
        if (job.payload or {}).get("lesson_id") == lesson_id:
            match = job
            break

    if match is None:
        match = create_job(
            db,
            "lesson_generation",
            {
                "lesson_id": row.id,
                "topic": row.topic,
                "language": row.language,
                "level": row.level,
                "user_id": row.user_id,
            },
        )
    elif match.status in {"completed", "failed"}:
        match.status = "queued"
        match.error = None
        match.progress = 0
        db.commit()

    enqueue(match.id, "lesson_generation")


def recover_unfinished_jobs() -> None:
    from app.db import SessionLocal

    db = SessionLocal()
    try:
        rows = db.query(LessonRow).filter(LessonRow.status.in_(("queued", "running"))).all()
        for row in rows:
            logger.info("resuming unfinished lesson %s (%s)", row.id, row.status)
            resume_lesson_job(db, row.id)
    except Exception:
        logger.exception("could not recover unfinished lesson jobs")
    finally:
        db.close()
