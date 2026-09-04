from __future__ import annotations

import json
import logging
import re
from typing import Any

from google import genai
from google.genai import types
from pydantic import BaseModel, ValidationError

from app.config import settings
from app.errors import AppError

logger = logging.getLogger(__name__)

MAX_RETRIES = 3


def require_gemini_key() -> str:
    key = settings.gemini_api_key.strip()
    if not key:
        raise AppError(
            status_code=503,
            error="Missing Gemini credentials",
            detail="GEMINI_API_KEY is not configured. Add it to backend/.env and restart the API.",
            code="missing_env",
            missing_keys=["GEMINI_API_KEY"],
        )
    return key


def get_genai_client() -> genai.Client:
    kwargs: dict[str, object] = {"api_key": require_gemini_key()}
    http_options = getattr(types, "HttpOptions", None)
    if http_options is not None:
        try:
            kwargs["http_options"] = http_options(timeout=90_000)
        except TypeError:
            pass
    if settings.google_genai_use_vertexai:
        kwargs["vertexai"] = True
    return genai.Client(**kwargs)  # type: ignore[arg-type]


def schema_for_gemini(schema: type[BaseModel]) -> dict[str, Any]:
    payload = schema.model_json_schema()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            node.pop("additionalProperties", None)
            node.pop("$schema", None)
            for value in list(node.values()):
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(payload)
    return payload


def extract_json(text: str) -> Any:
    raw = text.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)


def structured_generate(
    instruction: str,
    user_message: str,
    schema: type[BaseModel],
    *,
    temperature: float = 0.4,
    label: str = "Gemini",
) -> BaseModel:
    client = get_genai_client()
    last_error: Exception | None = None
    repair = ""
    for attempt in range(1, MAX_RETRIES + 1):
        prompt = (
            f"{instruction}\n\n"
            "Return JSON only. Match this schema:\n"
            f"{json.dumps(schema.model_json_schema(), indent=2)}\n\n"
            f"Student request:\n{user_message}"
        )
        if repair:
            prompt += (
                "\n\nYour previous JSON was invalid. Fix every schema error and return JSON only.\n"
                f"{repair}"
            )
        try:
            response = client.models.generate_content(
                model=settings.gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=temperature,
                ),
            )
        except Exception as exc:
            logger.exception("%s generate_content failed", label)
            last_error = exc
            continue

        raw_text = (response.text or "").strip()
        if not raw_text:
            last_error = ValueError("empty response")
            repair = "The model returned an empty body."
            continue
        try:
            return schema.model_validate_json(raw_text)
        except ValidationError as exc:
            last_error = exc
            repair = str(exc)
            try:
                payload = extract_json(raw_text)
                return schema.model_validate(payload)
            except (json.JSONDecodeError, ValidationError) as inner:
                last_error = inner
                repair = str(inner)
                logger.warning("%s schema validation failed attempt=%s error=%s", label, attempt, inner)

    raise AppError(
        status_code=502,
        error="The tutor could not build a valid lesson",
        detail=(
            f"{label} using {settings.gemini_model} returned invalid structured output "
            f"after {MAX_RETRIES} attempts: {last_error}"
        ),
        code="gemini_failed",
    )


def generate_text(instruction: str, user_message: str, *, temperature: float = 0.4) -> str:
    client = get_genai_client()
    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=f"{instruction}\n\n{user_message}",
        config=types.GenerateContentConfig(temperature=temperature),
    )
    text = (response.text or "").strip()
    if not text:
        raise AppError(
            status_code=502,
            error="Empty tutor reply",
            detail="Gemini returned no text. Try asking again.",
            code="gemini_failed",
        )
    return text
