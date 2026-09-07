#!/usr/bin/env python3
"""Clean polluted reel lessons: narration dumps, duration↔segments, bad audio, hashmap visual."""
from __future__ import annotations

import json
import re
import sqlite3
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "backend" / "tutor.db"
STORAGE = ROOT / "storage"


def strip_dump(narration: str, bullets: list[str] | None = None) -> str:
    text = (narration or "").strip()
    if not text:
        return text
    m = re.search(r"([।.])\s*1\.\s+[A-Za-z]", text)
    if m and m.start() > 40:
        return text[: m.start() + 1].strip()
    m = re.search(r"\s1\.\s+[A-Za-z].*2\.\s+[A-Za-z]", text)
    if m and m.start() > 40:
        return text[: m.start()].rstrip(" .।") + ("।" if "।" in text[: m.start()] else ".")
    if bullets:
        first = bullets[0]
        idx = text.find(first)
        if idx > 40 and re.search(rf"\d+\.\s*{re.escape(first)}", text[max(0, idx - 6) : idx + len(first) + 8]):
            prev = max(text.rfind("।", 0, idx), text.rfind(".", 0, idx))
            if prev > 20:
                return text[: prev + 1].strip()
    # collapse repeated joined bullet blocks
    if text.count("1. ") >= 3 and "2. " in text:
        m2 = re.search(r"1\.\s+", text)
        if m2 and m2.start() > 40:
            prev = max(text.rfind("।", 0, m2.start()), text.rfind(".", 0, m2.start()))
            if prev > 20:
                return text[: prev + 1].strip()
    return text


def rescale_segments(segments: list[dict], duration: float) -> list[dict]:
    if not segments or duration <= 0.2:
        return segments
    segs = []
    for s in segments:
        segs.append(
            {
                **s,
                "start": float(s.get("start") or 0),
                "end": float(s.get("end") or 0),
            }
        )
    last = max(s["end"] for s in segs) or 1.0
    if last <= 0.05:
        return segments
    scale = duration / last
    if abs(scale - 1.0) < 0.03:
        # still clamp ends
        out = []
        for s in segs:
            out.append({**s, "start": round(min(duration, s["start"]), 2), "end": round(min(duration, max(s["start"] + 0.05, s["end"])), 2)})
        if out:
            out[-1]["end"] = round(duration, 2)
        return out
    out = []
    for s in segs:
        start = round(s["start"] * scale, 2)
        end = round(s["end"] * scale, 2)
        out.append({**s, "start": start, "end": max(start + 0.05, end)})
    if out:
        out[-1]["end"] = round(duration, 2)
    return out


def wav_duration(url: str) -> float | None:
    if not url or not url.startswith("/audio/"):
        return None
    path = STORAGE / url.lstrip("/")
    if not path.exists():
        return None
    try:
        with wave.open(str(path), "rb") as w:
            return w.getnframes() / float(w.getframerate())
    except Exception:
        return None


def default_hashmap_visual() -> dict:
    return {
        "kind": "hashmap",
        "capacity": 8,
        "init_code": "Map<String, Integer> map = new HashMap<>();",
        "setup_lines": ["// Capacity = 8 buckets"],
        "puts": [
            {"code": 'map.put("Mia", 100);', "key": "Mia", "value": "100", "hash_bits": "01001011", "bucket": 3, "color": "orange"},
            {"code": 'map.put("Leo", 300);', "key": "Leo", "value": "300", "hash_bits": "00110011", "bucket": 3, "color": "green"},
        ],
        "node_fields": ["key", "value", "hash", "next"],
    }


def main() -> None:
    con = sqlite3.connect(DB)
    rows = con.execute("select id, topic, lesson_json from lessons").fetchall()
    changed = 0
    for lid, topic, raw in rows:
        lesson = raw if isinstance(raw, dict) else json.loads(raw)
        if isinstance(lesson, str):
            lesson = json.loads(lesson)
        if lesson.get("format") != "reel":
            continue
        dirty = False
        topic_l = (topic or lesson.get("topic") or "").lower()
        for scene in lesson.get("scenes") or []:
            bullets = [str(b).strip() for b in (scene.get("bullets") or []) if str(b).strip()]
            nar = scene.get("narration") or ""
            cleaned = strip_dump(nar, bullets)
            # prefer clean segments join if narration still polluted
            segs = scene.get("segments") or []
            seg_texts = [str(s.get("text") or "").strip() for s in segs if str(s.get("text") or "").strip()]
            if "1. " in cleaned and cleaned.count("1. ") >= 2 and seg_texts and all("1. " not in t for t in seg_texts):
                cleaned = " ".join(seg_texts)
            if cleaned != nar:
                scene["narration"] = cleaned
                dirty = True
            segs = scene.get("segments") or []
            last = max((float(s.get("end") or 0) for s in segs), default=0)
            dur = float(scene.get("duration") or 0)
            if segs and last > 0.5:
                # Prefer cue end as duration when planner wrote longer cues than fitted duration
                target = round(last, 1)
                # If duration was shorter, raise it to cues; then rescale if still mismatched
                if abs(dur - last) > 0.8:
                    # If cues are way longer than reel budget, shrink cues to duration instead
                    # Use max(dur, min(last, max(dur, word_est))) — practical: set duration to last when last < 45
                    if last <= 45:
                        scene["duration"] = target
                        dur = target
                        dirty = True
                    else:
                        scene["segments"] = rescale_segments(segs, max(dur, 8.0))
                        dirty = True
                        segs = scene["segments"]
                        last = max(float(s.get("end") or 0) for s in segs)
                        dur = float(scene.get("duration") or 0)
                # final rescale into duration
                if abs(last - dur) > 0.5 and dur > 0.5:
                    scene["segments"] = rescale_segments(segs, dur)
                    dirty = True
            audio = scene.get("audio_url") or ""
            adur = wav_duration(audio)
            last2 = max((float(s.get("end") or 0) for s in (scene.get("segments") or [])), default=0)
            if adur and last2 and adur > last2 + 12:
                scene["audio_url"] = None
                dirty = True
            elif adur and dur and adur > max(dur * 2.5, dur + 20):
                scene["audio_url"] = None
                dirty = True
            # hashmap visual
            if (
                scene.get("type") == "concept"
                and lesson.get("reel_mode") == "explainer"
                and ("hashmap" in topic_l or "hash map" in topic_l or "hashtable" in topic_l)
            ):
                vd = scene.get("visual_diagram") or {}
                if vd.get("kind") != "hashmap":
                    scene["visual_diagram"] = default_hashmap_visual()
                    dirty = True
        if dirty:
            # trim narration lengths for schema
            for scene in lesson.get("scenes") or []:
                nar = scene.get("narration") or ""
                if len(nar) > 2000:
                    scene["narration"] = nar[:1990].rstrip() + "।"
                    dirty = True
            con.execute(
                "update lessons set lesson_json=? where id=?",
                (json.dumps(lesson, ensure_ascii=False), lid),
            )
            changed += 1
            print("cleaned", lid, topic)
    con.commit()
    con.close()
    print(f"done, changed={changed}")


if __name__ == "__main__":
    main()
