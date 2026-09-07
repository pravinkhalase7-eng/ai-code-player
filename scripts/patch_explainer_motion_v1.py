#!/usr/bin/env python3
"""Explainer/info motion + viral thumbs: runtime fallback, intro/summary boards, THUMB bump."""
from pathlib import Path

ROOT = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder")

# ---------------------------------------------------------------------------
# 1) frontend/lib/explainerVisuals.ts — synthesize board steps when visual is empty
# ---------------------------------------------------------------------------
vis_path = ROOT / "frontend/lib/explainerVisuals.ts"
vis_path.write_text(
    '''/** Synthesize on-screen explainer/info board content when planner left visual empty. */

import type { Lesson, LessonScene } from "@/types/lesson";

export type BoardStep = { title: string; detail: string; example: string };

export function isExplainMotionLesson(lesson: Lesson): boolean {
  if (lesson.reel_mode === "explainer" || lesson.reel_mode === "info") return true;
  if (lesson.reel_mode === "code") return false;
  return lesson.requires_code === false;
}

function clip(text: string, max = 72): string {
  const t = String(text || "").replace(/\\s+/g, " ").trim();
  if (t.length <= max) return t;
  return `${t.slice(0, max - 1).trim()}…`;
}

function fromSegments(scene: LessonScene): BoardStep[] {
  return (scene.segments || [])
    .map((s) => {
      const text = String(s.text || "").trim();
      if (!text) return null;
      // Prefer first clause as title for cold-open / beat cards
      const title = clip(text.split(/[.!?]/)[0] || text, 48);
      return { title, detail: clip(text, 96), example: "" };
    })
    .filter(Boolean) as BoardStep[];
}

function fromNarration(scene: LessonScene): BoardStep[] {
  const narr = String(scene.narration || "").trim();
  if (!narr) return [];
  const parts = narr
    .split(/(?<=[.!?])\\s+/)
    .map((p) => p.trim())
    .filter((p) => p.length > 12);
  return parts.slice(0, 5).map((p) => ({
    title: clip(p.split(/[,:]/)[0] || p, 48),
    detail: clip(p, 96),
    example: "",
  }));
}

/** Build timed board steps for any explainer/info scene (intro / concept / summary). */
export function synthesizeBoardSteps(scene: LessonScene, lesson: Lesson): BoardStep[] {
  const diagram = (scene.diagram_steps || [])
    .map((s) => ({
      title: String(s.title || "").trim(),
      detail: String(s.detail || "").trim(),
      example: String(s.example || "").trim(),
    }))
    .filter((s) => s.title);
  if (diagram.length) return diagram;

  const bullets = (scene.bullets || []).map((b) => String(b || "").trim()).filter(Boolean);
  if (bullets.length) {
    return bullets.map((b) => ({ title: clip(b, 56), detail: "", example: "" }));
  }

  const takeaways = (scene.takeaways || []).map((t) => String(t || "").trim()).filter(Boolean);
  if (takeaways.length) {
    return takeaways.map((t) => ({ title: clip(t, 56), detail: "", example: "" }));
  }

  const callouts = (scene.visual?.callouts || []).map((c) => String(c || "").trim()).filter(Boolean);
  if (callouts.length) {
    return callouts.map((c) => ({ title: clip(c, 56), detail: "", example: "" }));
  }

  const segs = fromSegments(scene);
  if (segs.length >= 2) return segs;

  const narr = fromNarration(scene);
  if (narr.length) return narr;

  const topic = String(lesson.topic || lesson.title || "Key idea").trim();
  if (scene.type === "intro") {
    return [
      { title: "Wait — common myth", detail: clip(`Most people misunderstand ${topic}`, 80), example: "" },
      { title: "The real picture", detail: clip(`Here is why ${topic} actually matters`, 80), example: "" },
      { title: "Watch the stages", detail: "We break it into clear steps next", example: "" },
    ];
  }
  if (scene.type === "summary") {
    return [
      { title: "Save this", detail: clip(topic, 64), example: "" },
      { title: "Practice next", detail: "Try one tiny example today", example: "" },
      { title: "Follow for more", detail: "@techshalabypavi", example: "" },
    ];
  }
  return [{ title: clip(topic, 56), detail: clip(String(scene.narration || ""), 96), example: "" }];
}

export function boardKindLabel(scene: LessonScene): string {
  if (scene.type === "intro") return "Hook";
  if (scene.type === "summary") return "Takeaway";
  return "Explainer";
}
''',
    encoding="utf-8",
)
print("wrote explainerVisuals.ts")

# ---------------------------------------------------------------------------
# 2) frontend/types/lesson.ts — add visual field
# ---------------------------------------------------------------------------
types = ROOT / "frontend/types/lesson.ts"
tt = types.read_text(encoding="utf-8")
if "export type VisualSpec" not in tt:
    tt = tt.replace(
        "export type HashMapVisual = {",
        '''export type VisualSpec = {
  kind?: string;
  title?: string;
  callouts?: string[];
  particles?: boolean;
};

export type HashMapVisual = {''',
        1,
    )
if "visual?:" not in tt:
    tt = tt.replace(
        "  audio_url?: string | null;\n",
        "  audio_url?: string | null;\n  visual?: VisualSpec | null;\n",
        1,
    )
types.write_text(tt, encoding="utf-8")
print("types/lesson.ts ok")

# ---------------------------------------------------------------------------
# 3) ReelStage.tsx — animated boards for explainer intro/summary + synthesis
# ---------------------------------------------------------------------------
rs = ROOT / "frontend/components/player/ReelStage.tsx"
rt = rs.read_text(encoding="utf-8")

if 'from "@/lib/explainerVisuals"' not in rt:
    rt = rt.replace(
        'import { isPosterScene, reelCta } from "@/lib/reelCta";',
        'import { isPosterScene, reelCta } from "@/lib/reelCta";\n'
        'import { boardKindLabel, isExplainMotionLesson, synthesizeBoardSteps } from "@/lib/explainerVisuals";',
        1,
    )

old_block = '''  const poster = isPosterScene(scene.type);
  const thumb = lesson.thumbnail_url || "";
  const cta = reelCta(lesson, scene);
  const progress = duration > 0 ? Math.min(1, Math.max(0, currentTime / duration)) : 0;
  const isExplainer =
    lesson.reel_mode === "explainer" ||
    (lesson.reel_mode !== "info" && Boolean(scene.diagram_steps && scene.diagram_steps.length));
  const isConcept =
    scene.type === "concept" ||
    ((scene.type === "code" || scene.type === "execution") &&
      (!(code || "").trim() || lesson.requires_code === false));
  const diagramSteps = useMemo(() => {
    const steps = (scene.diagram_steps || [])
      .map((s) => ({
        title: String(s.title || "").trim(),
        detail: String(s.detail || "").trim(),
        example: String(s.example || "").trim(),
      }))
      .filter((s) => s.title);
    if (steps.length) return steps;
    return (scene.bullets || []).map((b) => ({ title: String(b || "").trim(), detail: "", example: "" })).filter((s) => s.title);
  }, [scene.diagram_steps, scene.bullets]);
'''

new_block = '''  const explainMotion = isExplainMotionLesson(lesson);
  // Code shorts keep static poster intros/summaries; explainer/info always get motion boards.
  const poster = isPosterScene(scene.type) && !explainMotion;
  const thumb = lesson.thumbnail_url || "";
  const cta = reelCta(lesson, scene);
  const progress = duration > 0 ? Math.min(1, Math.max(0, currentTime / duration)) : 0;
  const isExplainer =
    lesson.reel_mode === "explainer" ||
    (lesson.reel_mode !== "info" && Boolean(scene.diagram_steps && scene.diagram_steps.length));
  const isConcept =
    scene.type === "concept" ||
    (explainMotion && (scene.type === "intro" || scene.type === "summary")) ||
    ((scene.type === "code" || scene.type === "execution") &&
      (!(code || "").trim() || lesson.requires_code === false));
  const diagramSteps = useMemo(() => {
    // Prefer planner diagram_steps/bullets; else synthesize from visual/segments/narration
    // so kind:none never leaves a blank stage on explainer/info.
    return synthesizeBoardSteps(scene, lesson);
  }, [scene, lesson]);
'''

if old_block not in rt:
    raise SystemExit("ReelStage block missing — structure changed")
rt = rt.replace(old_block, new_block, 1)

# Chip label: Hook / Takeaway / Explainer
old_chip = '''              {isExplainer ? "Explainer" : "Explain"}
'''
new_chip = '''              {explainMotion ? boardKindLabel(scene) : isExplainer ? "Explainer" : "Explain"}
'''
if old_chip not in rt:
    raise SystemExit("chip label missing")
rt = rt.replace(old_chip, new_chip, 1)

# Cold-open hook flash for intro first 2.5s
old_header = '''          <header className="relative z-10 shrink-0 px-1 pt-2 text-center">
            <p
              className={cn(
                "info-step-chip inline-flex rounded-full border px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em]",
                isExplainer
                  ? "border-cyan-200/30 bg-cyan-300/10 text-cyan-100"
                  : "border-violet-200/30 bg-violet-300/10 text-violet-100",
              )}
            >
              {explainMotion ? boardKindLabel(scene) : isExplainer ? "Explainer" : "Explain"}
            </p>
            <h2 className="mt-2 line-clamp-2 text-2xl font-extrabold leading-7 tracking-tight text-white">{topic}</h2>
          </header>
'''
new_header = '''          <header className="relative z-10 shrink-0 px-1 pt-2 text-center">
            <p
              className={cn(
                "info-step-chip inline-flex rounded-full border px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em]",
                isExplainer || scene.type === "intro" || scene.type === "summary"
                  ? "border-cyan-200/30 bg-cyan-300/10 text-cyan-100"
                  : "border-violet-200/30 bg-violet-300/10 text-violet-100",
              )}
            >
              {explainMotion ? boardKindLabel(scene) : isExplainer ? "Explainer" : "Explain"}
            </p>
            {scene.type === "intro" && currentTime < 2.6 ? (
              <p className="reel-cta-pulse mt-2 inline-flex rounded-full bg-amber-400 px-4 py-1.5 text-sm font-extrabold uppercase tracking-wide text-zinc-950">
                {diagramSteps[0]?.title || "Wait for it…"}
              </p>
            ) : null}
            <h2 className="mt-2 line-clamp-2 text-2xl font-extrabold leading-7 tracking-tight text-white">{topic}</h2>
            {scene.type === "summary" && (scene.takeaways || []).length ? (
              <p className="mt-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-amber-200/90">
                End card · {Math.min((infoAnim?.visibleCount ?? 1), (scene.takeaways || []).length)} reveals
              </p>
            ) : null}
          </header>
'''
# infoAnim is declared after header currently — need to reorder carefully.
# Actually infoAnim is declared BEFORE the return, so it's available in JSX. Good.
# But in new_header I reference infoAnim which exists. OK.

if old_header not in rt:
    # try without the chip already replaced
    raise SystemExit("header block missing after chip replace")
rt = rt.replace(old_header, new_header, 1)

# For summary explainer: prefer takeaway bullets UI when no hashmap/diagram mechanism needed
# Current logic: isExplainer && diagramSteps → MechanismBoard. That works for synthesized steps too.
# For info mode (not explainer), bullets UI is used. Intro/summary on info will use bullets via:
# isExplainer false for pure info without diagram_steps — but synthesizeBoardSteps always returns steps,
# and isExplainer for info without diagram_steps is false... wait:
# isExplainer = reel_mode === "explainer" || (reel_mode !== "info" && diagram_steps)
# For info: isExplainer = false → goes to bullets UI with scene.bullets
# Problem: for info intro, bullets may be empty but diagramSteps synthesized — bullets UI shows narration only.
# Fix: use diagramSteps for bullet list when scene.bullets empty.

old_bullets = '''              {(scene.bullets || []).length ? (
                (scene.bullets || []).map((item, index) => {
'''
new_bullets = '''              {(diagramSteps.length ? diagramSteps.map((s) => s.title) : scene.bullets || []).length ? (
                (diagramSteps.length ? diagramSteps.map((s) => s.title) : scene.bullets || []).map((item, index) => {
'''
if old_bullets not in rt:
    raise SystemExit("bullets block missing")
rt = rt.replace(old_bullets, new_bullets, 1)

rs.write_text(rt, encoding="utf-8")
print("ReelStage.tsx ok")

# ---------------------------------------------------------------------------
# 4) reelCta — keep isPosterScene; motion decided in ReelStage
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# 5) reelExport.ts — same explainMotion poster bypass
# ---------------------------------------------------------------------------
ex = ROOT / "frontend/lib/reelExport.ts"
et = ex.read_text(encoding="utf-8")
if "isExplainMotionLesson" not in et:
    et = et.replace(
        'import { isPosterScene, reelCta } from "@/lib/reelCta";',
        'import { isPosterScene, reelCta } from "@/lib/reelCta";\n'
        'import { isExplainMotionLesson, synthesizeBoardSteps } from "@/lib/explainerVisuals";',
        1,
    )
old_poster = '''  const poster = isPosterScene(scene.type);
  if (poster) {
    if (!drawCoverImage(ctx, thumb)) drawStudioBackground(ctx);
  } else {
    drawStudioBackground(ctx);
  }
'''
new_poster = '''  const explainMotion = isExplainMotionLesson(lesson);
  const poster = isPosterScene(scene.type) && !explainMotion;
  if (poster) {
    if (!drawCoverImage(ctx, thumb)) drawStudioBackground(ctx);
  } else {
    drawStudioBackground(ctx);
  }
'''
if old_poster not in et:
    raise SystemExit("reelExport poster block missing")
et = et.replace(old_poster, new_poster, 1)

old_concept_if = '''  } else if (scene.type === "concept" || lesson.requires_code === false || lesson.reel_mode === "explainer") {
    drawConceptPanel(ctx, scene, elapsed, duration, topic, lesson);
'''
new_concept_if = '''  } else if (
    scene.type === "concept" ||
    explainMotion ||
    lesson.requires_code === false ||
    lesson.reel_mode === "explainer"
  ) {
    drawConceptPanel(ctx, scene, elapsed, duration, topic, lesson);
'''
if old_concept_if not in et:
    raise SystemExit("reelExport concept if missing")
et = et.replace(old_concept_if, new_concept_if, 1)

# Patch drawConceptPanel to use synthesizeBoardSteps for bullets
# Find where bullets are read
if "synthesizeBoardSteps" in et and "const boardSteps = synthesizeBoardSteps" not in et:
    # inject near drawConceptPanel bullets usage
    marker = "function drawConceptPanel("
    if marker not in et:
        raise SystemExit("drawConceptPanel missing")
# Look for bullets derivation inside drawConceptPanel
import re
m = re.search(
    r"(function drawConceptPanel\([\s\S]*?)(const bullets = .*?;)",
    et,
)
if m:
    et = et[: m.start(2)] + (
        "const synthesized = synthesizeBoardSteps(scene, lesson);\n"
        "  const bullets = synthesized.length\n"
        "    ? synthesized.map((s) => s.title)\n"
        "    : (scene.bullets || []).map((b) => String(b || \"\").trim()).filter(Boolean);\n"
        "  const _unusedBulletsLegacy = "
    ) + et[m.start(2) + len("const bullets = "):]
    # That hack is messy — do a cleaner replace
    raise SystemExit("need cleaner bullets patch")

ex.write_text(et, encoding="utf-8")
print("reelExport partial — will fix bullets next")
