from __future__ import annotations

import array
import math
import wave
from pathlib import Path

# Trim Chirp's long lead-in / tail only. Do NOT collapse mid-sentence pauses —
# karaoke and board cues are timed to those pauses, and squeezing them desyncs captions.
_LEAD_SEC = 0.04
_TAIL_SEC = 0.08
_FRAME_SEC = 0.02
_RMS_FLOOR = 520.0
_PEAK_RATIO = 0.08


def compact_wav_silence(path: Path | str) -> float | None:
    """Rewrite a 16-bit WAV in place, dropping leading/trailing silence.

    Returns the new duration in seconds, or None if the file was left unchanged.
    """
    dest = Path(path)
    if not dest.is_file():
        return None
    try:
        with wave.open(str(dest), "rb") as handle:
            channels = handle.getnchannels()
            sample_width = handle.getsampwidth()
            rate = handle.getframerate()
            frames = handle.getnframes()
            raw = handle.readframes(frames)
    except Exception:
        return None
    if sample_width != 2 or rate <= 0 or not raw or channels < 1:
        return None

    samples = array.array("h")
    samples.frombytes(raw)
    frame = max(1, int(rate * _FRAME_SEC) * channels)
    rms_values: list[float] = []
    for index in range(0, len(samples), frame):
        chunk = samples[index : index + frame]
        if not chunk:
            continue
        rms_values.append(math.sqrt(sum(sample * sample for sample in chunk) / max(1, len(chunk))))
    if not rms_values:
        return None

    peak = max(rms_values)
    floor = max(_RMS_FLOOR, peak * _PEAK_RATIO)
    first = next((i for i, rms in enumerate(rms_values) if rms >= floor), -1)
    last = next((i for i, rms in reversed(list(enumerate(rms_values))) if rms >= floor), -1)
    if first < 0 or last < 0 or last < first:
        return None

    lead = max(0, int(rate * _LEAD_SEC) * channels)
    tail = max(1, int(rate * _TAIL_SEC) * channels)
    start = max(0, first * frame - lead)
    end = min(len(samples), (last + 1) * frame + tail)
    if end - start < rate // 10:
        return None
    # Skip rewrite when we would only drop a few milliseconds.
    if start < frame and end >= len(samples) - frame:
        return len(samples) / float(rate * channels)

    out = array.array("h", samples[start:end])
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    try:
        with wave.open(str(tmp), "wb") as handle:
            handle.setnchannels(channels)
            handle.setsampwidth(sample_width)
            handle.setframerate(rate)
            handle.writeframes(out.tobytes())
        tmp.replace(dest)
    except Exception:
        tmp.unlink(missing_ok=True)
        return None
    return len(out) / float(rate * max(1, channels))
