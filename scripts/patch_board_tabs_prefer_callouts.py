#!/usr/bin/env python3
"""Prefer short callouts over narration segments for explainer board tabs.

Also: clean Hook/Takeaway/Explainer prefixes, dedupe title≈detail,
avoid ReelStage intro amber CTA duplicating board title, strip DB visual titles.
"""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LID = "les_c212bc5cac73491c94c42d877b1950a4"

NEW_VISUALS = r'''/** Synthesize on-screen explainer/info board content when planner left visual empty. */

import type { Lesson, LessonScene } from "@/types/lesson";

export type BoardStep = { title: string; detail: string; example: string };

export function isExplainMotionLesson(lesson: Lesson): boolean {
  if (lesson.reel_mode === "explainer" || lesson.reel_mode === "info") return true;
  if (lesson.reel_mode === "code") return false;
  return lesson.requires_code === false;
}

function clip(text: string, max = 72): string {
  const t = String(text || "").replace(/\s+/g, " ").trim();
  if (t.length <= max) return t;
  return `${t.slice(0, max - 1).trim()}…`;
}

/** Strip stage-kind labels baked into planner visual titles. */
export function cleanBoardTitle(text: string): string {
  return String(text || "")
    .replace(/^\s*(Hook|Takeaway|Explainer)\s*[·•:\-–—]\s*/i, "")
    .trim();
}

function normalizeForCompare(text: string): string {
  return String(text || "")
    .toLowerCase()
    .replace(/[^\w\s]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

/** Clear detail when it duplicates / prefixes / supersets the title. */
export function dedupeBoardDetail(title: string, detail: string): string {
  const t = normalizeForCompare(title);
  const d = normalizeForCompare(detail);
  if (!d) return "";
  if (!t) return String(detail || "").trim();
  if (d === t) return "";
  if (d.startsWith(t) || t.startsWith(d)) return "";
  if (d.includes(t) && d.length <= t.length + 24) return "";
  if (t.includes(d) && t.length <= d.length + 24) return "";
  return String(detail || "").trim();
}

function finalizeStep(step: BoardStep): BoardStep {
  const title = cleanBoardTitle(clip(step.title, 56));
  const detail = dedupeBoardDetail(title, cleanBoardTitle(step.detail));
  return {
    title,
    detail: detail ? clip(detail, 96) : "",
    example: String(step.example || "").trim(),
  };
}

/** Short punchy card title from a spoken segment — never the full caption. */
function punchyTitleFromSegment(text: string, index: number): string {
  const raw = String(text || "").replace(/\s+/g, " ").trim();
  if (!raw) return "";

  // Myth-style question → keep a short question
  if (/\?/.test(raw)) {
    const q = (raw.split("?")[0] || raw).trim();
    // Prefer a compact "X = Y?" / key-phrase feel when the question is long
    const syntax = q.match(/\b(confusing syntax|boilerplate|complex|hard to (?:read|learn))\b/i);
    if (syntax && q.length > 48) {
      return clip(`Python = ${syntax[1].toLowerCase()}?`, 44);
    }
    return clip(`${q}?`, 44);
  }

  // Contrast openers → truth line
  const contrast = raw.match(
    /^(?:Think again!?|Actually[,:]?|Nope[,:]?|Not quite[,:]?|Wrong[,:]?)\s*(.+)$/i,
  );
  if (contrast) {
    const rest = contrast[1].split(/[.!]/)[0] || contrast[1];
    if (/read like\s+(?:plain\s+)?English/i.test(rest) || /reads like/i.test(raw)) {
      return "Nope — it reads like English";
    }
    return clip(rest, 44);
  }

  if (/read(?:s)? like\s+(?:plain\s+)?English/i.test(raw)) {
    return index === 0 ? "Reads like English" : "Nope — it reads like English";
  }

  // First clause, hard-capped short — never paste the whole sentence as title+detail
  const clause = raw.split(/[.!]/)[0] || raw;
  if (clause.length > 42) {
    const words = clause.split(/\s+/).slice(0, 6).join(" ");
    return clip(words, 40);
  }
  return clip(clause, 40);
}

function fromSegments(scene: LessonScene): BoardStep[] {
  return (scene.segments || [])
    .map((s, index) => {
      const text = String(s.text || "").trim();
      if (!text) return null;
      const title = punchyTitleFromSegment(text, index);
      if (!title) return null;
      // Detail stays empty — karaoke already shows the full spoken line
      return finalizeStep({ title, detail: "", example: "" });
    })
    .filter(Boolean) as BoardStep[];
}

function fromNarration(scene: LessonScene): BoardStep[] {
  const narr = String(scene.narration || "").trim();
  if (!narr) return [];
  const parts = narr
    .split(/(?<=[.!?])\s+/)
    .map((p) => p.trim())
    .filter((p) => p.length > 12);
  return parts.slice(0, 5).map((p, index) =>
    finalizeStep({
      title: punchyTitleFromSegment(p, index),
      detail: "",
      example: "",
    }),
  );
}

/** Build timed board steps for any explainer/info scene (intro / concept / summary). */
export function synthesizeBoardSteps(scene: LessonScene, lesson: Lesson): BoardStep[] {
  const diagram = (scene.diagram_steps || [])
    .map((s) =>
      finalizeStep({
        title: String(s.title || "").trim(),
        detail: String(s.detail || "").trim(),
        example: String(s.example || "").trim(),
      }),
    )
    .filter((s) => s.title);
  if (diagram.length) return diagram;

  const bullets = (scene.bullets || []).map((b) => String(b || "").trim()).filter(Boolean);
  if (bullets.length) {
    return bullets.map((b) => finalizeStep({ title: b, detail: "", example: "" }));
  }

  const takeaways = (scene.takeaways || []).map((t) => String(t || "").trim()).filter(Boolean);
  if (takeaways.length) {
    return takeaways.map((t) => finalizeStep({ title: t, detail: "", example: "" }));
  }

  // Prefer short visual.callouts (myth→truth hooks) over raw narration segments.
  // Segments previously won for intro and painted full spoken sentences on the board.
  const callouts = (scene.visual?.callouts || []).map((c) => String(c || "").trim()).filter(Boolean);
  if (callouts.length) {
    return callouts.map((c) => finalizeStep({ title: c, detail: "", example: "" }));
  }

  const segs = fromSegments(scene);
  if (segs.length >= 1) return segs;

  const narr = fromNarration(scene);
  if (narr.length) return narr;

  const topic = cleanBoardTitle(String(lesson.topic || lesson.title || "Key idea").trim());
  if (scene.type === "intro") {
    return [
      finalizeStep({ title: "Wait — common myth", detail: `Most people misunderstand ${topic}`, example: "" }),
      finalizeStep({ title: "The real picture", detail: `Here is why ${topic} actually matters`, example: "" }),
      finalizeStep({ title: "Watch the stages", detail: "We break it into clear steps next", example: "" }),
    ];
  }
  if (scene.type === "summary") {
    return [
      finalizeStep({ title: "Save this", detail: topic, example: "" }),
      finalizeStep({ title: "Practice next", detail: "Try one tiny example today", example: "" }),
      finalizeStep({ title: "Follow for more", detail: "@techshalabypavi", example: "" }),
    ];
  }
  return [
    finalizeStep({
      title: topic,
      detail: String(scene.narration || ""),
      example: "",
    }),
  ];
}

export function boardKindLabel(scene: LessonScene): string {
  if (scene.type === "intro") return "Hook";
  if (scene.type === "summary") return "Takeaway";
  return "Explainer";
}
'''

def patch_explainer_visuals() -> None:
    path = ROOT / "frontend/lib/explainerVisuals.ts"
    path.write_text(NEW_VISUALS, encoding="utf-8")
    print("wrote explainerVisuals.ts")


def patch_mechanism_board() -> None:
    path = ROOT / "frontend/components/player/MechanismBoard.tsx"
    text = path.read_text(encoding="utf-8")

    # Ensure import of clean/dedupe helpers
    old_import = 'import { cn } from "@/lib/utils";'
    new_import = (
        'import { cn } from "@/lib/utils";\n'
        'import { cleanBoardTitle, dedupeBoardDetail } from "@/lib/explainerVisuals";'
    )
    if "cleanBoardTitle" not in text:
        if old_import not in text:
            raise SystemExit("MechanismBoard: cn import not found")
        text = text.replace(old_import, new_import, 1)

    old_block = """  const step = steps[safeActive] || { title: "", detail: "", example: "" };
  const example = String(phaseExample || step.example || "").trim();
  const title = String(phaseLabel || step.title || "").trim();
  const detail = String(step.detail || "").trim();
"""
    new_block = """  const step = steps[safeActive] || { title: "", detail: "", example: "" };
  const example = String(phaseExample || step.example || "").trim();
  const title = cleanBoardTitle(String(phaseLabel || step.title || "").trim());
  const rawDetail = String(step.detail || "").trim();
  // Avoid stacking detail that repeats / prefixes the title (common when steps came from narration).
  const detail = dedupeBoardDetail(title, rawDetail);
"""
    if old_block not in text:
        if "dedupeBoardDetail(title, rawDetail)" in text:
            print("MechanismBoard: already patched")
        else:
            raise SystemExit("MechanismBoard: title/detail block not found")
    else:
        text = text.replace(old_block, new_block, 1)
        print("MechanismBoard: dedupe + clean title")

    path.write_text(text, encoding="utf-8")


def patch_reel_stage() -> None:
    path = ROOT / "frontend/components/player/ReelStage.tsx"
    text = path.read_text(encoding="utf-8")

    old_import = (
        'import { boardKindLabel, isExplainMotionLesson, synthesizeBoardSteps } '
        'from "@/lib/explainerVisuals";'
    )
    new_import = (
        'import { boardKindLabel, cleanBoardTitle, isExplainMotionLesson, synthesizeBoardSteps } '
        'from "@/lib/explainerVisuals";'
    )
    if "cleanBoardTitle" not in text:
        if old_import not in text:
            raise SystemExit("ReelStage: explainerVisuals import not found")
        text = text.replace(old_import, new_import, 1)

    # Remove intro amber CTA that repeats the first board-tab title under the Hook chip.
    old_cta = """            {scene.type === \"intro\" && currentTime < 2.6 ? (
              <p className=\"reel-cta-pulse mt-2 inline-flex rounded-full bg-amber-400 px-4 py-1.5 text-sm font-extrabold uppercase tracking-wide text-zinc-950\">
                {diagramSteps[0]?.title || \"Wait for it…\"}
              </p>
            ) : null}
"""
    # Keep a non-duplicating pulse only when first title is empty (shouldn't happen with callouts).
    new_cta = """            {scene.type === \"intro\" && currentTime < 2.6 && !diagramSteps[0]?.title ? (
              <p className=\"reel-cta-pulse mt-2 inline-flex rounded-full bg-amber-400 px-4 py-1.5 text-sm font-extrabold uppercase tracking-wide text-zinc-950\">
                Wait for it…
              </p>
            ) : null}
"""
    if old_cta in text:
        text = text.replace(old_cta, new_cta, 1)
        print("ReelStage: removed redundant intro title pulse")
    elif "&& !diagramSteps[0]?.title" in text:
        print("ReelStage: intro pulse already gated")
    else:
        # Try looser match
        if "reel-cta-pulse mt-2 inline-flex rounded-full bg-amber-400" in text and "diagramSteps[0]?.title" in text:
            text2 = re.sub(
                r"\{scene\.type === \"intro\" && currentTime < 2\.6 \? \(\s*"
                r"<p className=\"reel-cta-pulse mt-2 inline-flex rounded-full bg-amber-400[^>]*>\s*"
                r"\{diagramSteps\[0\]\?\.title \|\| \"Wait for it…\"\}\s*"
                r"</p>\s*\) : null\}",
                '{scene.type === "intro" && currentTime < 2.6 && !diagramSteps[0]?.title ? (\n'
                '              <p className="reel-cta-pulse mt-2 inline-flex rounded-full bg-amber-400 px-4 py-1.5 text-sm font-extrabold uppercase tracking-wide text-zinc-950">\n'
                '                Wait for it…\n'
                '              </p>\n'
                '            ) : null}',
                text,
                count=1,
                flags=re.S,
            )
            if text2 == text:
                raise SystemExit("ReelStage: intro CTA block not matched")
            text = text2
            print("ReelStage: removed redundant intro title pulse (regex)")
        else:
            raise SystemExit("ReelStage: intro CTA block not found")

    path.write_text(text, encoding="utf-8")


def patch_lesson_db() -> None:
    db = ROOT / "backend/tutor.db"
    con = sqlite3.connect(db)
    row = con.execute("select lesson_json from lessons where id=?", (LID,)).fetchone()
    if not row:
        print("DB: lesson not found, skip")
        con.close()
        return
    lesson = json.loads(row[0])
    changed = False
    for s in lesson.get("scenes") or []:
        vis = s.get("visual") or {}
        title = str(vis.get("title") or "")
        cleaned = re.sub(
            r"^\s*(Hook|Takeaway|Explainer)\s*[·•:\-–—]\s*",
            "",
            title,
            flags=re.I,
        ).strip()
        if cleaned and cleaned != title:
            vis["title"] = cleaned
            s["visual"] = vis
            changed = True
            print(f"DB {s.get('type')}: title {title!r} -> {cleaned!r}")
        if s.get("type") == "intro":
            wanted = [
                "Python = confusing syntax?",
                "Nope — it reads like English",
                "Watch why pros pick it",
            ]
            if vis.get("callouts") != wanted:
                vis["callouts"] = wanted
                vis.setdefault("kind", "hook")
                vis.setdefault("particles", True)
                s["visual"] = vis
                changed = True
                print("DB intro: callouts ensured myth→truth")
    if changed:
        con.execute(
            "update lessons set lesson_json=? where id=?",
            (json.dumps(lesson, ensure_ascii=False), LID),
        )
        con.commit()
        print("DB updated")
    else:
        print("DB: no title/callout changes needed")
    con.close()


def main() -> None:
    patch_explainer_visuals()
    patch_mechanism_board()
    patch_reel_stage()
    patch_lesson_db()
    print("done")


if __name__ == "__main__":
    main()
