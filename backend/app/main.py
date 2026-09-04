import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import router as v1_router
from app.config import settings
from app.db import db_ready, init_db
from app.errors import AppError
from app.schemas.api import HealthResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _missing_keys() -> list[str]:
    missing: list[str] = []
    if not settings.gemini_api_key.strip():
        missing.append("GEMINI_API_KEY")
    if settings.tts_provider.lower() == "google" and not settings.google_tts_api_key.strip():
        missing.append("GOOGLE_TTS_API_KEY")
    return missing


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    Path(settings.storage_path).mkdir(parents=True, exist_ok=True)
    (Path(settings.storage_path) / "audio").mkdir(parents=True, exist_ok=True)
    (Path(settings.storage_path) / "images").mkdir(parents=True, exist_ok=True)
    try:
        init_db()
    except Exception:
        logger.exception("database init failed")
    try:
        from app.services.jobs import recover_unfinished_jobs

        recover_unfinished_jobs()
    except Exception:
        logger.exception("job recovery failed")
    yield


app = FastAPI(
    title="AI Coding Tutor",
    version="1.0.0",
    description="Interactive visual coding lessons with Gemini ADK, sandboxed execution, and Kokoro TTS.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
    + [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3010",
        "http://127.0.0.1:3010",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

audio_dir = Path(settings.storage_path) / "audio"
audio_dir.mkdir(parents=True, exist_ok=True)
images_dir = Path(settings.storage_path) / "images"
images_dir.mkdir(parents=True, exist_ok=True)
app.mount("/audio", StaticFiles(directory=str(audio_dir)), name="audio")
app.mount("/images", StaticFiles(directory=str(images_dir)), name="images")
app.include_router(v1_router, prefix="/api/v1")


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "ai-coding-tutor", "docs": "/docs"}


@app.exception_handler(AppError)
async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error,
            "detail": exc.detail,
            "code": exc.code,
            "missing_keys": exc.missing_keys,
        },
    )


@app.exception_handler(RequestValidationError)
async def request_validation_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"error": "Invalid request", "detail": str(exc.errors()), "code": "validation"},
    )


@app.get("/api/v1/health", response_model=HealthResponse)
def health() -> HealthResponse:
    missing = _missing_keys()
    runner = "unknown"
    try:
        import httpx

        response = httpx.get(settings.code_runner_url.rstrip("/") + "/health", timeout=1.5)
        runner = "ok" if response.status_code == 200 else "down"
    except Exception:
        runner = "down"
    status = "ok"
    if missing:
        status = "degraded"
    if not db_ready():
        status = "degraded"
    return HealthResponse(
        status=status,
        gemini_configured="GEMINI_API_KEY" not in missing,
        gemini_model=settings.gemini_model,
        tts_provider=settings.tts_provider,
        google_tts_configured=bool(settings.google_tts_api_key.strip()),
        code_runner=runner,
        missing_keys=missing,
    )
