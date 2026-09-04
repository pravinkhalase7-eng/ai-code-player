from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import settings
from app.errors import AppError
from app.models.orm import TtsCache
from app.services.tts.base import BrowserTTS, TTSProvider, tts_hash
from app.services.tts.gemini_tts import GeminiTTS
from app.services.tts.google_tts import GoogleTTS
from app.services.tts.kokoro import KokoroTTS

logger = logging.getLogger(__name__)

MIN_AUDIO_BYTES = 256
GOOGLE_CACHE_TAG = "google:linear16-24k"


def cache_provider_key(provider_name: str) -> str:
    if provider_name.lower() == "google":
        return GOOGLE_CACHE_TAG
    return provider_name.lower()


PROVIDERS: dict[str, TTSProvider] = {
    "google": GoogleTTS(),
    "kokoro": KokoroTTS(),
    "gemini": GeminiTTS(),
    "browser": BrowserTTS(),
}


def get_provider(name: str) -> TTSProvider:
    provider = PROVIDERS.get(name.lower())
    if provider is None:
        raise AppError(
            status_code=500,
            error="Unknown TTS provider",
            detail=f"{name} is not configured.",
            code="tts_failed",
        )
    return provider


def audio_file_ready(url: str | None) -> bool:
    if not url:
        return False
    stored = Path(settings.storage_path) / "audio" / Path(url).name
    return stored.exists() and stored.stat().st_size >= MIN_AUDIO_BYTES


def _usable_file(path: Path) -> bool:
    return path.exists() and path.stat().st_size >= MIN_AUDIO_BYTES


def synthesize_narration(
    db: Session,
    text: str,
    *,
    voice: str | None = None,
    speed: float | None = None,
    provider_name: str | None = None,
) -> tuple[str, str]:
    provider_name = (provider_name or settings.tts_provider).lower()
    requested_voice = voice or settings.tts_voice
    speed = speed if speed is not None else settings.tts_speed
    cache_id = tts_hash(text, requested_voice, speed, cache_provider_key(provider_name))
    cached = db.get(TtsCache, cache_id)
    if cached:
        stored = Path(settings.storage_path) / "audio" / Path(cached.path).name
        if _usable_file(stored):
            return cached.path, cached.provider

    dest_dir = Path(settings.storage_path) / "audio"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{cache_id}.mp3"

    providers = [provider_name]
    fallback = (settings.tts_fallback_provider or "").lower()
    if fallback and fallback not in providers:
        providers.append(fallback)
    if (
        provider_name not in {"browser", "google"}
        and fallback != "browser"
        and settings.google_tts_api_key.strip()
        and "google" not in providers
    ):
        providers.append("google")

    seen: set[str] = set()
    used = provider_name
    produced: Path | None = None
    for name in providers:
        name = name.lower()
        if name in seen or name == "browser":
            continue
        seen.add(name)
        try:
            written = get_provider(name).synthesize(text, requested_voice, speed, dest)
            if _usable_file(written):
                used = name
                produced = written
                break
        except Exception as exc:
            logger.warning("TTS provider %s failed: %s", name, exc)
            continue

    if produced is None:
        return "", "browser"

    public_path = f"/audio/{produced.name}"
    db.merge(
        TtsCache(
            id=cache_id,
            provider=used,
            voice=requested_voice,
            text=text,
            path=public_path,
        )
    )
    db.commit()
    return public_path, used
