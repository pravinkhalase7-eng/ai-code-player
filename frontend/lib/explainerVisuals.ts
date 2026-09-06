/** Synthesize on-screen explainer/info board content when planner left visual empty. */

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
