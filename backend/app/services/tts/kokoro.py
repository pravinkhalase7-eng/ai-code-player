from __future__ import annotations

import logging
from pathlib import Path

import httpx

from app.config import settings
from app.errors import AppError
from app.services.tts.base import TTSProvider

logger = logging.getLogger(__name__)


class KokoroTTS(TTSProvider):
    name = "kokoro"

    def synthesize(self, text: str, voice: str, speed: float, dest: Path) -> Path:
        url = settings.kokoro_url.rstrip("/") + "/v1/audio/speech"
        payload = {
            "model": "kokoro",
            "input": text,
            "voice": voice or settings.tts_voice,
            "speed": speed,
            "response_format": "mp3",
        }
        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
        except Exception as exc:
            raise AppError(
                status_code=502,
                error="Kokoro TTS failed",
                detail=str(exc),
                code="tts_failed",
            ) from exc
        dest.write_bytes(response.content)
        if dest.stat().st_size < 32:
            raise AppError(
                status_code=502,
                error="Kokoro TTS failed",
                detail="Kokoro returned empty audio.",
                code="tts_failed",
            )
        return dest
