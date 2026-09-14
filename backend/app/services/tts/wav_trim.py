from __future__ import annotations

import array
import math
import wave
from pathlib import Path

# Keep a little air so consonants are not clipped, but collapse Chirp's
# long sentence-final pauses that make downloaded reels feel stalled.
_MAX_GAP_SEC = 0.12
_LEAD_SEC = 0.03
_TAIL_SEC = 0.06
_FRAME_SEC = 0.02
_RMS_FLOOR = 480.0


def compact_wav_silence(path: Path | str) -> float | None:
    """Rewrite a 16-bit WAV in place, collapsing long silent gaps.

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
    if sample_width != 2 or rate <= 0 or not raw:
        return None

    samples = array.array("h")
    samples.frombytes(raw)
    frame = max(1, int(rate * _FRAME_SEC))
    kept: list[int] = []
    silent_run: list[int] = []
    heard = False
    max_gap = max(1, int(rate * _MAX_GAP_SEC) * channels)
    lead = max(0, int(rate * _LEAD_SEC) * channels)

    def flush_silence(final: bool = False) -> None:
        if not silent_run:
            return
        if not heard:
            if final:
                return
            kept.extend(silent_run[-lead:] if lead else [])
            silent_run.clear()
            return
        keep = min(len(silent_run), max_gap)
        if final:
            keep = min(len(silent_run), max(1, int(rate * _TAIL_SEC) * channels))
        kept.extend(silent_run[:keep])
        silent_run.clear()

    for index in range(0, len(samples), frame * channels):
        chunk = samples[index : index + frame * channels]
        if not chunk:
            continue
        rms = math.sqrt(sum(sample * sample for sample in chunk) / max(1, len(chunk)))
        if rms >= _RMS_FLOOR:
            flush_silence()
            heard = True
            kept.extend(chunk)
        else:
            silent_run.extend(chunk)
    flush_silence(final=True)

    if not heard or len(kept) < rate // 10:
        return None

    out = array.array("h", kept)
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
