from __future__ import annotations

import logging
from pathlib import Path

from google.genai import types

from app.config import settings
from app.errors import AppError
from app.services.gemini_client import get_genai_client
from app.services.tts.base import TTSProvider, wrap_pcm_wav

logger = logging.getLogger(__name__)


class GeminiTTS(TTSProvider):
    name = "gemini"

    def synthesize(self, text: str, voice: str, speed: float, dest: Path) -> Path:
        client = get_genai_client()
        try:
            response = client.models.generate_content(
                model=settings.gemini_tts_model,
                contents=text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name="Kore",
                            )
                        )
                    ),
                ),
            )
        except Exception as exc:
            raise AppError(
                status_code=502,
                error="Gemini TTS failed",
                detail=str(exc),
                code="tts_failed",
            ) from exc

        data = b""
        try:
            data = response.candidates[0].content.parts[0].inline_data.data  # type: ignore[union-attr]
        except Exception as exc:
            raise AppError(
                status_code=502,
                error="Gemini TTS failed",
                detail=f"No audio bytes returned: {exc}",
                code="tts_failed",
            ) from exc
        if len(data) < 64:
            raise AppError(
                status_code=502,
                error="Gemini TTS failed",
                detail="Gemini returned empty audio.",
                code="tts_failed",
            )
        if data[:4] != b"RIFF" and data[:3] != b"ID3" and data[:2] != b"\xff\xfb":
            dest = dest.with_suffix(".wav")
            dest.write_bytes(wrap_pcm_wav(data))
        else:
            dest.write_bytes(data)
        return dest
