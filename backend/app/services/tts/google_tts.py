from __future__ import annotations

import base64
import logging
import re
from pathlib import Path

import httpx

from app.config import settings
from app.errors import AppError
from app.services.locale import candidate_voices
from app.services.tts.base import TTSProvider

logger = logging.getLogger(__name__)

TTS_ENDPOINT = "https://texttospeech.googleapis.com/v1/text:synthesize"
DEFAULT_VOICE = "en-US-Chirp3-HD-Aoede"
VOICE_RE = re.compile(r"^[a-z]{2,3}-[A-Z]{2}-.+$")
# MP3 from Cloud TTS is ~32 kbps and sounds thin. LINEAR16 24 kHz WAV is what Chirp 3 HD is produced at.
ENCODINGS: tuple[tuple[str, int | None, str], ...] = (
    ("LINEAR16", 24000, ".wav"),
    ("LINEAR16", None, ".wav"),
    ("MP3", None, ".mp3"),
)


def resolve_cloud_voice(voice: str) -> tuple[str, str]:
    name = (voice or "").strip() or DEFAULT_VOICE
    if not VOICE_RE.match(name):
        name = DEFAULT_VOICE
    language = "-".join(name.split("-")[:2])
    return name, language


class GoogleTTS(TTSProvider):
    """Google Cloud Text-to-Speech with Chirp 3 HD voices and uncompressed audio."""

    name = "google"

    def synthesize(self, text: str, voice: str, speed: float, dest: Path) -> Path:
        key = settings.google_tts_api_key.strip()
        if not key:
            raise AppError(
                status_code=503,
                error="Missing Google Cloud TTS credentials",
                detail="Set GOOGLE_TTS_API_KEY to use Cloud Text-to-Speech.",
                code="tts_failed",
                missing_keys=["GOOGLE_TTS_API_KEY"],
            )
        requested, _language = resolve_cloud_voice(voice)
        candidates = candidate_voices(requested)

        last_error = "Cloud Text-to-Speech returned no audio."
        for voice_name in candidates:
            language = "-".join(voice_name.split("-")[:2])
            for encoding, sample_rate, suffix in ENCODINGS:
                response = self._synthesize_request(
                    key, text, voice_name, language, speed, encoding, sample_rate
                )
                if response.status_code >= 400:
                    last_error = response.text[:400] or f"HTTP {response.status_code}"
                    logger.warning(
                        "Google Cloud voice %s %s failed: %s",
                        voice_name,
                        encoding,
                        last_error,
                    )
                    continue
                audio_b64 = str(response.json().get("audioContent") or "")
                if not audio_b64:
                    continue
                out = dest.with_suffix(suffix)
                out.write_bytes(base64.b64decode(audio_b64))
                if out.stat().st_size < 256:
                    out.unlink(missing_ok=True)
                    continue
                logger.info(
                    "Google Cloud TTS wrote %s (%s bytes, voice=%s, encoding=%s)",
                    out.name,
                    out.stat().st_size,
                    voice_name,
                    encoding,
                )
                return out

        raise AppError(
            status_code=502,
            error="Google Cloud TTS failed",
            detail=last_error,
            code="tts_failed",
        )

    def _synthesize_request(
        self,
        key: str,
        text: str,
        voice_name: str,
        language: str,
        speed: float,
        encoding: str,
        sample_rate: int | None,
    ) -> httpx.Response:
        audio_config: dict[str, object] = {
            "audioEncoding": encoding,
            "speakingRate": round(max(0.85, min(1.05, speed if speed else 0.96)), 2),
        }
        if sample_rate:
            audio_config["sampleRateHertz"] = sample_rate
        payload = {
            "input": {"text": text[:4500]},
            "voice": {"languageCode": language, "name": voice_name},
            "audioConfig": audio_config,
        }
        try:
            return httpx.post(
                TTS_ENDPOINT,
                params={"key": key},
                json=payload,
                timeout=60.0,
            )
        except Exception as exc:
            raise AppError(
                status_code=502,
                error="Google Cloud TTS failed",
                detail=str(exc),
                code="tts_failed",
            ) from exc
