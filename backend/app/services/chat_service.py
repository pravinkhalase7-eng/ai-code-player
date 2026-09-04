from __future__ import annotations

from sqlalchemy.orm import Session

from app.agents.orchestrator import chat_reply
from app.config import settings
from app.errors import AppError
from app.models.orm import ChatMessage, LessonRow, TutorSession
from app.schemas.api import ExecuteResult
from app.schemas.lesson import ChatReply
from app.services.lesson_service import record_execution


def get_or_create_session(db: Session, user_id: str, lesson_id: str) -> TutorSession:
    row = (
        db.query(TutorSession)
        .filter(TutorSession.user_id == user_id, TutorSession.lesson_id == lesson_id)
        .order_by(TutorSession.created_at.desc())
        .first()
    )
    if row is None:
        row = TutorSession(user_id=user_id, lesson_id=lesson_id)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def ask_tutor(db: Session, lesson_id: str, message: str, user_id: str | None) -> tuple[ChatReply, ExecuteResult | None]:
    uid = user_id or settings.default_user_id
    lesson = db.get(LessonRow, lesson_id)
    if lesson is None or not lesson.lesson_json:
        raise AppError(404, "Lesson not found", "Generate a lesson first, then ask follow-up questions.", "not_found")
    session = get_or_create_session(db, uid, lesson_id)
    db.add(ChatMessage(session_id=session.id, role="student", content=message))
    db.commit()

    reply = chat_reply(str(lesson.lesson_json), message)
    execution = None
    lowered = message.lower()
    should_run = reply.should_execute or "run" in lowered or "remove i++" in lowered or "infinite" in lowered
    code = reply.code
    language = reply.language or lesson.language
    if should_run:
        if not code:
            for scene in lesson.lesson_json.get("scenes", []):
                if scene.get("type") in {"code", "execution"} and scene.get("code"):
                    code = scene["code"]
                    break
        if code and "remove i++" in lowered:
            code = code.replace("i++", "").replace("++i", "")
        if code:
            execution = record_execution(db, uid, lesson_id, language, code)
            if execution.timed_out:
                reply = reply.model_copy(
                    update={
                        "reply": (
                            reply.reply
                            + " Execution stopped because the program exceeded the time limit. "
                            "Without i++ the condition never becomes false, so the loop never ends."
                        )
                    }
                )
    db.add(ChatMessage(session_id=session.id, role="tutor", content=reply.reply))
    db.commit()
    return reply, execution
