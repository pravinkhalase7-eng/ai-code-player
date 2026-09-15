from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

from app.services.tts.wav_trim import compact_wav_silence


def _write_wav(path: Path, samples: list[int], rate: int = 8000) -> None:
    raw = struct.pack("<" + "h" * len(samples), *samples)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(raw)


def _tone(rate: int, seconds: float, freq: float = 440.0) -> list[int]:
    count = int(rate * seconds)
    return [int(12000 * math.sin(2 * math.pi * freq * index / rate)) for index in range(count)]


def _duration(path: Path) -> float:
    with wave.open(str(path), "rb") as handle:
        return handle.getnframes() / float(handle.getframerate())


def test_compact_wav_silence_trims_trailing(tmp_path: Path) -> None:
    dest = tmp_path / "tail.wav"
    rate = 8000
    samples = _tone(rate, 0.4) + [0] * int(rate * 1.6)
    _write_wav(dest, samples, rate)
    before = _duration(dest)
    compact_wav_silence(dest)
    after = _duration(dest)
    assert before > 1.8
    assert after < 0.7
    assert after > 0.35


def test_compact_wav_silence_keeps_internal_pause(tmp_path: Path) -> None:
    dest = tmp_path / "pause.wav"
    rate = 8000
    samples = _tone(rate, 0.35) + [0] * int(rate * 0.45) + _tone(rate, 0.35, 520)
    _write_wav(dest, samples, rate)
    before = _duration(dest)
    compact_wav_silence(dest)
    after = _duration(dest)
    # Mid-sentence pause must remain so captions stay on the spoken clock.
    assert after > before - 0.2
    assert after > 1.0
