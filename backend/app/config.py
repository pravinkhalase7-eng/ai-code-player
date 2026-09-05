from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent
DEFAULT_STORAGE = REPO_ROOT / "storage"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+psycopg://tutor:tutor@localhost:5432/aicoder"
    redis_url: str = "redis://localhost:6379/0"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.6-flash"
    gemini_image_model: str = "gemini-3.1-flash-image"
    gemini_tts_model: str = "gemini-2.5-flash-preview-tts"
    google_genai_use_vertexai: bool = False
    google_tts_api_key: str = ""

    tts_provider: str = "google"
    tts_fallback_provider: str = "google"
    tts_voice: str = "en-US-Chirp3-HD-Aoede"
    tts_speed: float = 0.96
    kokoro_url: str = "http://localhost:8880"

    image_provider: str = "local"
    remotion_renderer_url: str = "http://localhost:3000"

    storage_provider: str = "local"
    storage_path: Path = DEFAULT_STORAGE

    code_runner_url: str = "http://localhost:8090"
    code_execution_timeout: int = 5
    code_execution_memory_mb: int = 256
    code_execution_cpu_limit: float = 1
    code_execution_output_limit: int = 65536
    code_execution_pids_limit: int = 32

    cors_origins: str = "http://localhost:3000"
    node_env: str = "development"
    default_user_id: str = "demo-user"

    celery_eager: bool = False
    use_celery: bool = False


settings = Settings()
