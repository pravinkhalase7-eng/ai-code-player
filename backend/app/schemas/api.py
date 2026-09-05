from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

from app.schemas.lesson import (
    EvaluationResult,
    ExecutionStep,
    Lesson,
    LessonFormat,
    LessonLevel,
    ReelSceneScript,
    normalize_reel_seconds,
)
from app.services.locale import normalize_spoken_language
from app.services.visualizer import normalize_language


class LessonCreateRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=200)
    language: str = Field(default="java", min_length=1, max_length=32)
    spoken_language: str = Field(default="en", min_length=1, max_length=32)
    level: LessonLevel = LessonLevel.beginner
    format: LessonFormat = LessonFormat.lesson
    user_id: str | None = None
    reel_seconds: int = 30
    requires_code: bool | None = None

    @field_validator("language")
    @classmethod
    def _language(cls, value: str) -> str:
        return normalize_language(value)

    @field_validator("spoken_language")
    @classmethod
    def _spoken(cls, value: str) -> str:
        return normalize_spoken_language(value)

    @field_validator("reel_seconds")
    @classmethod
    def _reel_seconds(cls, value: int) -> int:
        return normalize_reel_seconds(value)


class LessonCreateResponse(BaseModel):
    lesson_id: str
    status: str
    job_id: str | None = None


class ChatRequest(BaseModel):
    lesson_id: str
    message: str = Field(min_length=1, max_length=2000)
    user_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    expression: str
    execution: dict | None = None
    mini_visualization: dict | None = None


class ExecuteRequest(BaseModel):
    language: str = "java"
    code: str = Field(min_length=1, max_length=50_000)
    lesson_id: str | None = None
    user_id: str | None = None

    @field_validator("language")
    @classmethod
    def _language(cls, value: str) -> str:
        return normalize_language(value)


class ExecuteResult(BaseModel):
    success: bool
    stdout: list[str] = Field(default_factory=list)
    stderr: str = ""
    execution_time_ms: int = 0
    timed_out: bool = False
    compile_error: bool = False
    job_id: str | None = None
    status: str = "completed"
    iterations: list[ExecutionStep] = Field(default_factory=list)


class RunHelpRequest(BaseModel):
    language: str = "java"
    code: str = Field(min_length=1, max_length=50_000)
    stderr: str = ""
    compile_error: bool = False
    timed_out: bool = False
    lesson_id: str | None = None

    @field_validator("language")
    @classmethod
    def _language(cls, value: str) -> str:
        return normalize_language(value)


class RunHelpResponse(BaseModel):
    issue: str
    explanation: str
    line: int | None = None
    label: str = "error"
    suggested_code: str | None = None


class QuizAnswerRequest(BaseModel):
    answer: int | str | None = None
    code: str | None = None
    user_id: str | None = None
    time_spent_ms: int = 0
    hints_used: int = 0


class QuizAnswerResponse(BaseModel):
    evaluation: EvaluationResult
    mastery: float | None = None


class ProgressResponse(BaseModel):
    lesson_id: str
    current_scene: str | None = None
    completion_percent: float
    score: float
    scene_index: int = 0
    time_spent_ms: int = 0


class ProgressUpdateRequest(BaseModel):
    current_scene: str | None = None
    scene_index: int = 0
    completion_percent: float = 0
    score: float | None = None
    time_spent_ms: int = 0
    user_id: str | None = None


class JobResponse(BaseModel):
    job_id: str
    kind: str
    status: str
    progress: float = 0
    error: str | None = None
    result: dict | None = None
    created_at: datetime | None = None


class HealthResponse(BaseModel):
    status: str
    gemini_configured: bool
    gemini_model: str
    tts_provider: str
    google_tts_configured: bool = False
    code_runner: str
    missing_keys: list[str] = Field(default_factory=list)


class LessonResponse(BaseModel):
    lesson: Lesson
    status: str
    warnings: list[str] = Field(default_factory=list)


class ReelScriptRequest(BaseModel):
    code: str | None = Field(default=None, max_length=50_000)
    scenes: list[ReelSceneScript] = Field(default_factory=list)
    rewrite: bool = False


def new_id(prefix: str = "") -> str:
    value = uuid4().hex
    return f"{prefix}{value}" if prefix else value
