from __future__ import annotations

import logging

import httpx

from app.config import settings
from app.errors import AppError
from app.schemas.api import ExecuteResult
from app.services.visualizer import ensure_runnable

logger = logging.getLogger(__name__)


class ExecutionAgent:
    """Prepares untrusted code for the isolated sandbox. Never runs it locally."""

    def prepare(self, language: str, code: str) -> dict[str, str | int]:
        return {
            "language": language.lower(),
            "code": code,
            "timeout": settings.code_execution_timeout,
        }


def execute_in_sandbox(language: str, code: str) -> ExecuteResult:
    payload = ExecutionAgent().prepare(language, ensure_runnable(language, code))
    url = settings.code_runner_url.rstrip("/") + "/execute"
    try:
        with httpx.Client(timeout=settings.code_execution_timeout + 8) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError as exc:
        logger.exception("code-runner unreachable")
        raise AppError(
            status_code=503,
            error="Code sandbox unavailable",
            detail=(
                "The isolated code runner is not reachable. "
                "Start it with docker compose, then try running the code again."
            ),
            code="sandbox_unavailable",
        ) from exc
    return ExecuteResult.model_validate(data)
