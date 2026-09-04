#!/usr/bin/env python3
"""Rewrite localhost URLs so Docker Compose services can reach each other."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def upsert(text: str, key: str, value: str) -> str:
    pattern = re.compile(rf"^{re.escape(key)}=.*$", re.M)
    line = f"{key}={value}"
    if pattern.search(text):
        return pattern.sub(lambda _m: line, text)
    return text.rstrip() + "\n" + line + "\n"


def read_value(text: str, key: str, default: str = "") -> str:
    match = re.search(rf"^{re.escape(key)}=(.*)$", text, re.M)
    if not match:
        return default
    return match.group(1).strip().strip("'").strip('"')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("env_file")
    parser.add_argument("--public-app-url", default="")
    args = parser.parse_args()

    path = Path(args.env_file)
    text = path.read_text()

    user = read_value(text, "POSTGRES_USER", "tutor")
    password = read_value(text, "POSTGRES_PASSWORD", "tutor")
    db = read_value(text, "POSTGRES_DB", "aicoder")

    text = upsert(text, "DATABASE_URL", f"postgresql+psycopg://{user}:{password}@postgres:5432/{db}")
    text = upsert(text, "REDIS_URL", "redis://redis:6379/0")
    text = upsert(text, "CODE_RUNNER_URL", "http://code-runner:8090")
    text = upsert(text, "KOKORO_URL", "http://kokoro:8880")
    text = upsert(text, "STORAGE_PATH", "/data")
    text = upsert(text, "USE_CELERY", "true")
    text = upsert(text, "API_ORIGIN", "http://backend:8000")

    public = (args.public_app_url or "").strip().rstrip("/")
    if public:
        text = upsert(text, "CORS_ORIGINS", f"{public},http://localhost:3010,http://localhost:3000")
        text = upsert(text, "NEXT_PUBLIC_API_URL", public)

    if not read_value(text, "GEMINI_API_KEY"):
        raise SystemExit("ERROR: GEMINI_API_KEY is empty in the secret file. Fill it, re-upload, rebuild.")

    path.write_text(text if text.endswith("\n") else text + "\n")
    print("normalized", path)


if __name__ == "__main__":
    main()
