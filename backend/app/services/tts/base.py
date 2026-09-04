from __future__ import annotations

import hashlib
import struct
from abc import ABC, abstractmethod
from pathlib import Path

from app.errors import AppError


def tts_hash(text: str, voice: str, speed: float, provider: str) -> str:
    payload = f"{text}|{voice}|{speed}|{provider}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def wrap_pcm_wav(pcm: bytes, sample_rate: int = 24000) -> bytes:
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + len(pcm),
        b"WAVE",
        b"fmt ",
        16,
        1,
        1,
        sample_rate,
        sample_rate * 2,
        2,
        16,
        b"data",
        len(pcm),
    )
    return header + pcm


class TTSProvider(ABC):
    name: str

    @abstractmethod
    def synthesize(self, text: str, voice: str, speed: float, dest: Path) -> Path:
        raise NotImplementedError


class BrowserTTS(TTSProvider):
    """Client-side Web Speech API. Does not produce an audio file."""

    name = "browser"

    def synthesize(self, text: str, voice: str, speed: float, dest: Path) -> Path:
        raise AppError(
            status_code=501,
            error="Browser TTS has no server audio",
            detail="Use the Web Speech API in the lesson player.",
            code="tts_browser",
        )
