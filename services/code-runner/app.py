from __future__ import annotations

import logging
import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from executor import execute

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("code-runner")

app = FastAPI(title="AI Coder Sandbox", version="1.0.0")


class ExecuteIn(BaseModel):
    language: str = Field(min_length=1, max_length=32)
    code: str = Field(min_length=1, max_length=50_000)
    timeout: int | None = Field(default=None, ge=1, le=15)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "code-runner"}


@app.post("/execute")
def run_code(payload: ExecuteIn) -> dict:
    try:
        result = execute(payload.language, payload.code, payload.timeout)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        logger.exception("sandbox crashed")
        raise HTTPException(status_code=500, detail="Sandbox failed") from exc
    return result.as_dict()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8090")),
    )
