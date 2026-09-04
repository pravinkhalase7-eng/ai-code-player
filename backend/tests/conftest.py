import os
from pathlib import Path

TEST_DB = Path(__file__).parent / "test.db"
if TEST_DB.exists():
    TEST_DB.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"
os.environ["GEMINI_API_KEY"] = ""
os.environ.setdefault("CODE_RUNNER_URL", "http://127.0.0.1:9")
os.environ.setdefault("TTS_PROVIDER", "browser")
os.environ.setdefault("TTS_FALLBACK_PROVIDER", "browser")

