from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def uid() -> str:
    return uuid4().hex


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    display_name: Mapped[str] = mapped_column(String(120), default="Student")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    lessons: Mapped[list["LessonRow"]] = relationship(back_populates="user")


class LessonRow(Base):
    __tablename__ = "lessons"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(160))
    language: Mapped[str] = mapped_column(String(32), default="java")
    level: Mapped[str] = mapped_column(String(32), default="beginner")
    topic: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(32), default="queued")
    lesson_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    warnings: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user: Mapped[User] = relationship(back_populates="lessons")
    scenes: Mapped[list["LessonSceneRow"]] = relationship(back_populates="lesson", cascade="all, delete-orphan")
    progress: Mapped[list["LessonProgress"]] = relationship(back_populates="lesson")


class LessonSceneRow(Base):
    __tablename__ = "lesson_scenes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    lesson_id: Mapped[str] = mapped_column(ForeignKey("lessons.id"), index=True)
    scene_id: Mapped[str] = mapped_column(String(64))
    type: Mapped[str] = mapped_column(String(32))
    position: Mapped[int] = mapped_column(Integer, default=0)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    lesson: Mapped[LessonRow] = relationship(back_populates="scenes")


class LessonProgress(Base):
    __tablename__ = "lesson_progress"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    lesson_id: Mapped[str] = mapped_column(ForeignKey("lessons.id"), index=True)
    current_scene: Mapped[str | None] = mapped_column(String(64), nullable=True)
    scene_index: Mapped[int] = mapped_column(Integer, default=0)
    completion_percent: Mapped[float] = mapped_column(Float, default=0)
    score: Mapped[float] = mapped_column(Float, default=0)
    time_spent_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    lesson: Mapped[LessonRow] = relationship(back_populates="progress")


class Concept(Base):
    __tablename__ = "concepts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    language: Mapped[str] = mapped_column(String(32), default="java")


class UserConcept(Base):
    __tablename__ = "user_concepts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    concept_id: Mapped[str] = mapped_column(ForeignKey("concepts.id"), index=True)
    mastery: Mapped[float] = mapped_column(Float, default=0)
    failed_questions: Mapped[int] = mapped_column(Integer, default=0)
    hints: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class CodeExample(Base):
    __tablename__ = "code_examples"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    lesson_id: Mapped[str] = mapped_column(ForeignKey("lessons.id"), index=True)
    language: Mapped[str] = mapped_column(String(32))
    code: Mapped[str] = mapped_column(Text)
    verified_output: Mapped[list[str]] = mapped_column(JSON, default=list)


class CodeExecution(Base):
    __tablename__ = "code_executions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    user_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    lesson_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    language: Mapped[str] = mapped_column(String(32))
    code: Mapped[str] = mapped_column(Text)
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    stdout: Mapped[list[str]] = mapped_column(JSON, default=list)
    stderr: Mapped[str] = mapped_column(Text, default="")
    execution_time_ms: Mapped[int] = mapped_column(Integer, default=0)
    timed_out: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    lesson_id: Mapped[str] = mapped_column(ForeignKey("lessons.id"), index=True)
    scene_id: Mapped[str] = mapped_column(String(64))
    kind: Mapped[str] = mapped_column(String(32))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    question_id: Mapped[str] = mapped_column(ForeignKey("quiz_questions.id"), index=True)
    answer: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class TtsCache(Base):
    __tablename__ = "tts_cache"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    provider: Mapped[str] = mapped_column(String(32))
    voice: Mapped[str] = mapped_column(String(64))
    text: Mapped[str] = mapped_column(Text)
    path: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class GeneratedAsset(Base):
    __tablename__ = "generated_assets"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    kind: Mapped[str] = mapped_column(String(32))
    prompt: Mapped[str] = mapped_column(Text, default="")
    model: Mapped[str] = mapped_column(String(80), default="")
    path: Mapped[str] = mapped_column(String(500))
    meta: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class TutorSession(Base):
    __tablename__ = "tutor_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    lesson_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    messages: Mapped[list["ChatMessage"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    session_id: Mapped[str] = mapped_column(ForeignKey("tutor_sessions.id"), index=True)
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    session: Mapped[TutorSession] = relationship(back_populates="messages")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    kind: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), default="queued")
    progress: Mapped[float] = mapped_column(Float, default=0)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
