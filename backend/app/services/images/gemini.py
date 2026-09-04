from __future__ import annotations

from pathlib import Path

from google.genai import types

from app.config import settings
from app.errors import AppError
from app.services.gemini_client import get_genai_client
from app.services.images.base import ImageProvider


class GeminiImage(ImageProvider):
    name = "gemini"

    def generate(self, prompt: str, dest: Path, *, aspect_ratio: str, seed: int, style: str) -> Path:
        client = get_genai_client()
        try:
            response = client.models.generate_content(
                model=settings.gemini_image_model,
                contents=f"{style} educational illustration, aspect {aspect_ratio}, seed {seed}. {prompt}",
                config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
            )
        except Exception as exc:
            raise AppError(
                status_code=502,
                error="Image generation failed",
                detail=str(exc),
                code="image_failed",
            ) from exc
        try:
            data = response.candidates[0].content.parts[0].inline_data.data  # type: ignore[union-attr]
        except Exception as exc:
            raise AppError(
                status_code=502,
                error="Image generation failed",
                detail=f"No image bytes: {exc}",
                code="image_failed",
            ) from exc
        dest.write_bytes(data)
        return dest
