#!/usr/bin/env python3
"""Simulate synthesizeBoardSteps priority for intro (mirrors TS logic)."""
from __future__ import annotations

import json
import re
import sqlite3
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LID = "les_c212bc5cac73491c94c42d877b1950a4"


def clean_board_title(text: str) -> str:
    return re.sub(r"^\s*(Hook|Takeaway|Explainer)\s*[·•:\-–—]\s*", "", text or "", flags=re.I).strip()


def clip(text: str, max_len: int = 72) -> str:
    t = re.sub(r"\s+", " ", text or "").strip()
    if len(t) <= max_len:
        return t
    return t[: max_len - 1].rstrip() + "…"


def synthesize(scene: dict, lesson: dict) -> list[dict]:
    diagram = []
    for s in scene.get("diagram_steps") or []:
        title = clean_board_title(str(s.get("title") or "").strip())
        if title:
            diagram.append(
                {
                    "title": title,
                    "detail": str(s.get("detail") or "").strip(),
                    "example": str(s.get("example") or "").strip(),
                    "src": "diagram",
                }
            )
    if diagram:
        return diagram

    bullets = [str(b).strip() for b in (scene.get("bullets") or []) if str(b).strip()]
    if bullets:
        return [{"title": clip(b, 56), "detail": "", "example": "", "src": "bullets"} for b in bullets]

    takeaways = [str(t).strip() for t in (scene.get("takeaways") or []) if str(t).strip()]
    if takeaways:
        return [{"title": clip(t, 56), "detail": "", "example": "", "src": "takeaways"} for t in takeaways]

    callouts = [
        str(c).strip()
        for c in ((scene.get("visual") or {}).get("callouts") or [])
        if str(c).strip()
    ]
    if callouts:
        return [
            {"title": clip(clean_board_title(c), 56), "detail": "", "example": "", "src": "callouts"}
            for c in callouts
        ]

    segs = []
    for s in scene.get("segments") or []:
        text = str(s.get("text") or "").strip()
        if not text:
            continue
        segs.append({"title": clip(text, 40), "detail": "", "example": "", "src": "segments"})
    if segs:
        return segs
    return [{"title": "fallback", "detail": "", "example": "", "src": "fallback"}]


def load_lesson() -> dict:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:8010/api/v1/lesson/{LID}", timeout=10) as r:
            d = json.load(r)
        return d.get("lesson") or d
    except Exception as e:
        print("API unavailable, reading DB:", e)
        con = sqlite3.connect(ROOT / "backend/tutor.db")
        raw = con.execute("select lesson_json from lessons where id=?", (LID,)).fetchone()[0]
        con.close()
        return json.loads(raw)


def check_files() -> None:
    vis = (ROOT / "frontend/lib/explainerVisuals.ts").read_text()
    assert "scene.type === \"intro\" && segs.length >= 1) return segs" not in vis
    assert "cleanBoardTitle" in vis
    assert "dedupeBoardDetail" in vis
    assert "punchyTitleFromSegment" in vis
    i_call = vis.find("scene.visual?.callouts")
    i_seg_return = vis.find("const segs = fromSegments")
    assert 0 <= i_call < i_seg_return, "callouts must be before fromSegments fallback"
    # old bad priority comment gone / new comment present
    assert "Prefer short visual.callouts" in vis
    mb = (ROOT / "frontend/components/player/MechanismBoard.tsx").read_text()
    assert "dedupeBoardDetail" in mb
    assert "cleanBoardTitle" in mb
    rs = (ROOT / "frontend/components/player/ReelStage.tsx").read_text()
    assert "!diagramSteps[0]?.title" in rs
    print("file_assertions_ok")


def main() -> None:
    check_files()
    lesson = load_lesson()
    print("title:", lesson.get("title"))
    for scene in lesson.get("scenes") or []:
        steps = synthesize(scene, lesson)
        print("=" * 56, scene.get("type"))
        print("visual.title:", (scene.get("visual") or {}).get("title"))
        print("callouts:", (scene.get("visual") or {}).get("callouts"))
        print("board steps:")
        for i, st in enumerate(steps):
            print(f"  [{i}] src={st['src']!r} title={st['title']!r} detail={st['detail']!r}")
        if scene.get("type") == "intro":
            titles = [st["title"] for st in steps]
            assert steps and steps[0]["src"] == "callouts", steps
            assert "Think Python is just another" not in " ".join(titles)
            assert "Python = confusing syntax?" in titles
            assert "Nope — it reads like English" in titles
            print("INTRO_OK: short callouts, not full narration")
        if scene.get("type") == "concept":
            assert steps[0]["src"] == "diagram"
            assert steps[0]["title"] == "Human-Readable Syntax"
            print("CONCEPT_OK: diagram_steps unchanged")
    print("verify_ok")


if __name__ == "__main__":
    main()
