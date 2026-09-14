from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

from app.services.tts.wav_trim import compact_wav_silence


def _write_tone_silence_tone(path: Path, rate: int = 8000) -> None:
    tone = int(rate * 0.4)
    silence = int(rate * 0.9)
    samples: list[int] = []
    for index in range(tone):
        samples.append(int(12000 * math.sin(2 * math.pi * 440 * index / rate)))
    samples.extend([0] * silence)
    for index in range(tone):
        samples.append(int(12000 * math.sin(2 * math.pi * 440 * index / rate)))
    raw = struct.pack("<" + "h" * len(samples), *samples)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(raw)


def test_compact_wav_silence_collapses_long_gap(tmp_path: Path) -> None:
    dest = tmp_path / "gap.wav"
    _write_tone_silence_tone(dest)
    with wave.open(str(dest), "rb") as handle:
        before = handle.getnframes() / float(handle.getframerate())
    compact_wav_silence(dest)
    with wave.open(str(dest), "rb") as handle:
        after = handle.getnframes() / float(handle.getframerate())
    assert before > 1.6
    assert after < before - 0.5
    assert after > 0.7
