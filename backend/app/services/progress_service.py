from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.orm import LessonProgress, UserConcept
from app.schemas.lesson import EvaluationResult


def get_or_create_progress(db: Session, user_id: str, lesson_id: str) -> LessonProgress:
    row = (
        db.query(LessonProgress)
        .filter(LessonProgress.user_id == user_id, LessonProgress.lesson_id == lesson_id)
        .order_by(LessonProgress.created_at.asc())
        .first()
    )
    if row is None:
        row = LessonProgress(user_id=user_id, lesson_id=lesson_id)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def update_progress(
    db: Session,
    user_id: str,
    lesson_id: str,
    *,
    current_scene: str | None,
    scene_index: int,
    completion_percent: float,
    score: float | None,
    time_spent_ms: int,
) -> LessonProgress:
    row = get_or_create_progress(db, user_id, lesson_id)
    row.current_scene = current_scene
    row.scene_index = scene_index
    row.completion_percent = max(row.completion_percent, min(100.0, completion_percent))
    if score is not None:
        row.score = score
    row.time_spent_ms = max(row.time_spent_ms, time_spent_ms)
    db.commit()
    db.refresh(row)
    return row


def adjust_mastery(
    db: Session,
    user_id: str,
    concept_id: str,
    evaluation: EvaluationResult,
    hints_used: int,
) -> float:
    row = (
        db.query(UserConcept)
        .filter(UserConcept.user_id == user_id, UserConcept.concept_id == concept_id)
        .one_or_none()
    )
    if row is None:
        row = UserConcept(user_id=user_id, concept_id=concept_id, mastery=0.4, hints=0, failed_questions=0)
        db.add(row)
    row.mastery = max(0.0, min(1.0, (row.mastery or 0) + evaluation.mastery_delta - 0.02 * hints_used))
    if evaluation.status != "correct":
        row.failed_questions = (row.failed_questions or 0) + 1
    row.hints = (row.hints or 0) + hints_used
    db.commit()
    return row.mastery
