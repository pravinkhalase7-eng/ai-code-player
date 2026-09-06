from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.errors import AppError
from app.models.orm import Job, LessonRow
from app.schemas.api import (
    ChatRequest,
    ChatResponse,
    ExecuteRequest,
    ExecuteResult,
    JobResponse,
    LessonCreateRequest,
    LessonCreateResponse,
    LessonResponse,
    ProgressResponse,
    ProgressUpdateRequest,
    QuizAnswerRequest,
    QuizAnswerResponse,
    ReelScriptRequest,
    RunHelpRequest,
    RunHelpResponse,
)
from app.schemas.lesson import Lesson
from app.services.images.thumbnail import THUMB_VERSION
from app.services.chat_service import ask_tutor
from app.services.jobs import create_job, enqueue, resume_lesson_job
from app.services.lesson_service import (
    delete_lesson,
    list_recent_lessons,
    queue_lesson,
    record_execution,
    schedule_google_audio,
    lesson_needs_google_audio,
    schedule_reel_thumbnail,
    lesson_needs_sandbox_rerun,
    schedule_sandbox_rerun,
    refresh_reel_thumbnail,
    update_reel_script,
)
from app.services.progress_service import get_or_create_progress, update_progress
from app.services.quiz_service import evaluate_quiz
from app.services.run_help import explain_run_error

router = APIRouter()


@router.post("/tutor/lesson", response_model=LessonCreateResponse)
def create_lesson(payload: LessonCreateRequest, db: Session = Depends(get_db)) -> LessonCreateResponse:
    lesson_id, job_id = queue_lesson(
        db,
        topic=payload.topic.strip(),
        language=payload.language.strip() or "java",
        level=payload.level.value,
        user_id=payload.user_id,
        format=payload.format.value,
        spoken_language=payload.spoken_language,
        reel_seconds=payload.reel_seconds,
        requires_code=payload.requires_code,
    )
    return LessonCreateResponse(lesson_id=lesson_id, status="queued", job_id=job_id)


@router.post("/tutor/chat", response_model=ChatResponse)
def tutor_chat(payload: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    reply, execution = ask_tutor(db, payload.lesson_id, payload.message.strip(), payload.user_id)
    return ChatResponse(
        reply=reply.reply,
        expression=reply.expression.value,
        execution=execution.model_dump() if execution else None,
        mini_visualization=reply.mini_visualization.model_dump() if reply.mini_visualization else None,
    )


@router.post("/code/execute", response_model=ExecuteResult)
def execute_code(payload: ExecuteRequest, db: Session = Depends(get_db)) -> ExecuteResult:
    return record_execution(
        db,
        payload.user_id or settings.default_user_id,
        payload.lesson_id,
        payload.language,
        payload.code,
    )


@router.post("/code/run-help", response_model=RunHelpResponse)
def run_help(payload: RunHelpRequest, db: Session = Depends(get_db)) -> RunHelpResponse:
    topic = ""
    spoken_language = "en"
    if payload.lesson_id:
        row = db.get(LessonRow, payload.lesson_id)
        if row is not None:
            topic = row.topic
            spoken_language = (row.lesson_json or {}).get("spoken_language") or "en"
    help_text = explain_run_error(
        language=payload.language,
        code=payload.code,
        stderr=payload.stderr,
        compile_error=payload.compile_error,
        timed_out=payload.timed_out,
        topic=topic,
        spoken_language=spoken_language,
    )
    return RunHelpResponse(
        issue=help_text.issue,
        explanation=help_text.explanation,
        line=help_text.line,
        label=help_text.label,
        suggested_code=help_text.suggested_code,
    )


@router.get("/lesson/{lesson_id}", response_model=LessonResponse)
def get_lesson(lesson_id: str, db: Session = Depends(get_db)) -> LessonResponse:
    row = db.get(LessonRow, lesson_id)
    if row is None:
        raise AppError(404, "Lesson not found", "That lesson does not exist.", "not_found")
    if row.status != "ready" or not row.lesson_json:
        if row.status in {"queued", "running"}:
            resume_lesson_job(db, row.id)
        return LessonResponse(
            lesson=Lesson.model_construct(
                lesson_id=row.id,
                title=row.title,
                language=row.language,
                level=row.level,  # type: ignore[arg-type]
                topic=row.topic,
                objectives=["Generating your lesson..."],
                scenes=[],
            )
            if False
            else _pending_lesson(row),
            status=row.status,
            warnings=row.warnings or [],
        )
    lesson = Lesson.model_validate(row.lesson_json)
    if lesson_needs_google_audio(lesson):
        schedule_google_audio(row.id)
    elif lesson_needs_sandbox_rerun(lesson):
        schedule_sandbox_rerun(row.id)
    if lesson.format.value == "reel" and f"v={THUMB_VERSION}" not in (lesson.thumbnail_url or ""):
        schedule_reel_thumbnail(row.id)
    return LessonResponse(lesson=lesson, status=row.status, warnings=row.warnings or [])


def _pending_lesson(row: LessonRow) -> Lesson:
    from app.schemas.lesson import CodeScene, IntroScene, QuizScene, SummaryScene

    fmt = (row.lesson_json or {}).get("format") or "lesson"
    spoken = (row.lesson_json or {}).get("spoken_language") or "en"
    if fmt == "reel":
        from app.schemas.lesson import ConceptScene

        explain = (row.lesson_json or {}).get("requires_code") is False
        pending_middle = (
            ConceptScene(
                id="scene_concept_pending",
                duration=12,
                narration="The explanation bullets will appear next.",
                bullets=["Preparing the idea...", "No program in this info reel"],
            )
            if explain
            else CodeScene(
                id="scene_code_pending",
                duration=10,
                narration="The example will appear next.",
                code="public class Main {\n    public static void main(String[] args) {\n    }\n}\n",
            )
        )
        return Lesson(
            lesson_id=row.id,
            title=row.title,
            language=row.language,
            spoken_language=spoken,
            level=row.level,  # type: ignore[arg-type]
            format="reel",  # type: ignore[arg-type]
            topic=row.topic,
            objectives=["Cutting a short"],
            requires_code=not explain,
            scenes=[
                IntroScene(id="scene_pending", duration=6, narration="Give me a moment while I cut this short."),
                pending_middle,
                SummaryScene(
                    id="scene_summary_pending",
                    duration=5,
                    narration="A punchy takeaway is next.",
                    takeaways=["Almost ready"],
                ),
            ],
        )
    return Lesson(
        lesson_id=row.id,
        title=row.title,
        language=row.language,
        spoken_language=spoken,
        level=row.level,  # type: ignore[arg-type]
        topic=row.topic,
        objectives=["Building a visual lesson"],
        scenes=[
            IntroScene(id="scene_pending", duration=6, narration="Give me a moment while I prepare this lesson."),
            CodeScene(
                id="scene_code_pending",
                duration=8,
                narration="Your code editor will appear next.",
                code="public class Main {\n    public static void main(String[] args) {\n    }\n}\n",
            ),
            QuizScene(
                id="scene_quiz_pending",
                duration=8,
                narration="A question will appear after the explanation.",
                question="Lesson is still generating. Please wait.",
                options=["Working...", "Still working...", "Almost ready", "Ready soon"],
                answer=0,
            ),
        ],
    )


@router.get("/lessons")
def get_lessons(user_id: str | None = None, db: Session = Depends(get_db)) -> dict:
    uid = user_id or settings.default_user_id
    return {"lessons": list_recent_lessons(db, uid)}


@router.delete("/lesson/{lesson_id}")
def remove_lesson(lesson_id: str, db: Session = Depends(get_db)) -> dict:
    delete_lesson(db, lesson_id)
    return {"ok": True, "lesson_id": lesson_id}


@router.get("/lesson/{lesson_id}/progress", response_model=ProgressResponse)
def get_progress(lesson_id: str, user_id: str | None = None, db: Session = Depends(get_db)) -> ProgressResponse:
    row = get_or_create_progress(db, user_id or settings.default_user_id, lesson_id)
    return ProgressResponse(
        lesson_id=lesson_id,
        current_scene=row.current_scene,
        completion_percent=row.completion_percent,
        score=row.score,
        scene_index=row.scene_index,
        time_spent_ms=row.time_spent_ms,
    )


@router.post("/lesson/{lesson_id}/progress", response_model=ProgressResponse)
def post_progress(
    lesson_id: str,
    payload: ProgressUpdateRequest,
    db: Session = Depends(get_db),
) -> ProgressResponse:
    row = update_progress(
        db,
        payload.user_id or settings.default_user_id,
        lesson_id,
        current_scene=payload.current_scene,
        scene_index=payload.scene_index,
        completion_percent=payload.completion_percent,
        score=payload.score,
        time_spent_ms=payload.time_spent_ms,
    )
    return ProgressResponse(
        lesson_id=lesson_id,
        current_scene=row.current_scene,
        completion_percent=row.completion_percent,
        score=row.score,
        scene_index=row.scene_index,
        time_spent_ms=row.time_spent_ms,
    )


@router.post("/lesson/{lesson_id}/thumbnail", response_model=LessonResponse)
def post_thumbnail(lesson_id: str, db: Session = Depends(get_db)) -> LessonResponse:
    row = db.get(LessonRow, lesson_id)
    if row is None:
        raise AppError(404, "Lesson not found", "That lesson does not exist.", "not_found")
    lesson = refresh_reel_thumbnail(db, lesson_id)
    return LessonResponse(lesson=lesson, status=row.status, warnings=row.warnings or [])


@router.post("/lesson/{lesson_id}/script", response_model=LessonResponse)
def post_reel_script(lesson_id: str, payload: ReelScriptRequest, db: Session = Depends(get_db)) -> LessonResponse:
    row = db.get(LessonRow, lesson_id)
    if row is None:
        raise AppError(404, "Lesson not found", "That lesson does not exist.", "not_found")
    lesson = update_reel_script(
        db,
        lesson_id,
        code=payload.code,
        scenes=payload.scenes,
        rewrite=payload.rewrite,
    )
    return LessonResponse(lesson=lesson, status=row.status, warnings=row.warnings or [])


@router.post("/lesson/{lesson_id}/render", response_model=JobResponse)
def render_lesson(lesson_id: str, db: Session = Depends(get_db)) -> JobResponse:
    row = db.get(LessonRow, lesson_id)
    if row is None:
        raise AppError(404, "Lesson not found", "That lesson does not exist.", "not_found")
    job = create_job(db, "video_render", {"lesson_id": lesson_id})
    enqueue(job.id, "video_render")
    return JobResponse(job_id=job.id, kind=job.kind, status=job.status, progress=job.progress)


@router.post("/quiz/{question_id}/answer", response_model=QuizAnswerResponse)
def answer_quiz(
    question_id: str,
    payload: QuizAnswerRequest,
    db: Session = Depends(get_db),
) -> QuizAnswerResponse:
    evaluation, mastery = evaluate_quiz(
        db,
        question_id,
        payload.user_id or settings.default_user_id,
        payload.answer,
        payload.code,
        payload.hints_used,
    )
    return QuizAnswerResponse(evaluation=evaluation, mastery=mastery)


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str, db: Session = Depends(get_db)) -> JobResponse:
    job = db.get(Job, job_id)
    if job is None:
        raise AppError(404, "Job not found", "That job does not exist.", "not_found")
    return JobResponse(
        job_id=job.id,
        kind=job.kind,
        status=job.status,
        progress=job.progress,
        error=job.error,
        result=job.result,
        created_at=job.created_at,
    )
