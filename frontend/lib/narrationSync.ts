import { highlightForSpeech, progressiveHighlight } from "@/lib/codeFocus";
import type { HighlightRange, LessonScene, TutorExpression } from "@/types/lesson";

export type SyncCue = {
  start: number;
  end: number;
  text: string;
  highlight: HighlightRange | null;
  expression?: TutorExpression;
  stepIndex?: number;
};

export function splitSentences(text: string): string[] {
  return text
    .split(/(?<=[.!?।])\s+|\n+/)
    .map((part) => part.trim())
    .filter(Boolean);
}

export function estimatedSpeechDuration(text: string, fallback = 8): number {
  const words = text.trim().split(/\s+/).filter(Boolean).length;
  if (!words) return fallback;
  return Math.max(3, words / 2.45);
}

function clipDuration(scene: LessonScene, audioDuration?: number): number {
  if (typeof audioDuration === "number" && Number.isFinite(audioDuration) && audioDuration > 0.4) {
    return audioDuration;
  }
  return estimatedSpeechDuration(scene.narration || "", scene.duration || 8);
}

function weightedCues(
  scene: LessonScene,
  parts: { text: string; key?: string | null; expression?: TutorExpression }[],
  duration: number,
): SyncCue[] {
  if (!parts.length) {
    return [
      {
        start: 0,
        end: duration,
        text: scene.narration || "",
        highlight: progressiveHighlight(scene.code || "", scene.highlight_ranges ?? [], scene.narration || "", 0, 1),
      },
    ];
  }
  const weights = parts.map((part) => Math.max(1, part.text.split(/\s+/).filter(Boolean).length));
  const total = weights.reduce((sum, value) => sum + value, 0);
  let cursor = 0;
  return parts.map((part, index) => {
    const span = duration * (weights[index] / total);
    const start = cursor;
    cursor += span;
    return {
      start,
      end: index === parts.length - 1 ? duration + 0.05 : cursor,
      text: part.text,
      expression: part.expression,
      highlight: progressiveHighlight(
        scene.code || "",
        scene.highlight_ranges ?? [],
        part.text,
        index,
        parts.length,
        part.key,
      ),
    };
  });
}

export function buildCues(scene: LessonScene, audioDuration?: number): SyncCue[] {
  const duration = clipDuration(scene, audioDuration);
  const code = scene.code || "";

  if (scene.type === "execution" && scene.iterations?.length) {
    const steps = scene.iterations;
    const spokenParts: { text: string }[] = [];
    for (const segment of scene.segments ?? []) {
      const bits = splitSentences(segment.text || "");
      if (bits.length) bits.forEach((text) => spokenParts.push({ text }));
      else if (segment.text?.trim()) spokenParts.push({ text: segment.text });
    }
    if (!spokenParts.length) {
      for (const text of splitSentences(scene.narration || "")) spokenParts.push({ text });
    }
    const speechCues = spokenParts.length
      ? weightedCues(scene, spokenParts, duration)
      : weightedCues(
          scene,
          steps.map((step) => ({ text: (step.description || step.label || "step").trim() || "step" })),
          duration,
        );
    const assigned = matchStepsToCues(steps, speechCues, code);
    return speechCues.map((cue, index) => {
      const stepIndex = assigned[index];
      const step = typeof stepIndex === "number" ? steps[stepIndex] : undefined;
      return {
        ...cue,
        highlight: step
          ? {
              start_line: step.line || 1,
              end_line: step.line || 1,
              start_col: 0,
              label: step.label || "step",
            }
          : cue.highlight,
        stepIndex,
      };
    });
  }

  // Code explain: prefer fine-grained sentence cues so the selection keeps moving.
  if (scene.type === "code") {
    const segments = scene.segments ?? [];
    const sentenceParts: { text: string; key?: string | null; expression?: TutorExpression }[] = [];
    if (segments.length) {
      for (const segment of segments) {
        const bits = splitSentences(segment.text || "");
        if (bits.length) {
          bits.forEach((text, bitIndex) => {
            sentenceParts.push({
              text,
              key: bitIndex === 0 ? segment.highlight : null,
              expression: segment.expression,
            });
          });
        } else if (segment.text?.trim()) {
          sentenceParts.push({
            text: segment.text,
            key: segment.highlight,
            expression: segment.expression,
          });
        }
      }
    }
    if (!sentenceParts.length) {
      for (const text of splitSentences(scene.narration || "")) {
        sentenceParts.push({ text });
      }
    }
    return weightedCues(scene, sentenceParts, duration);
  }

  const segments = scene.segments ?? [];
  if (segments.length >= 1) {
    const last = Math.max(...segments.map((segment) => segment.end), 0.1);
    const scale = duration / last;
    return segments.map((segment, index) => ({
      start: segment.start * scale,
      end: segment.end * scale,
      text: segment.text,
      highlight: progressiveHighlight(
        code,
        scene.highlight_ranges ?? [],
        segment.text,
        index,
        segments.length,
        segment.highlight,
      ),
      expression: segment.expression,
    }));
  }

  const sentences = splitSentences(scene.narration || "");
  return weightedCues(
    scene,
    sentences.map((text) => ({ text })),
    duration,
  );
}

function tokenizeSpeech(text: string): string[] {
  return (text || "")
    .toLowerCase()
    .replace(/[^a-z0-9_\s.+-]/g, " ")
    .split(/\s+/)
    .filter((word) => word.length > 1);
}

function stepSpeechScore(
  step: { description?: string; label?: string; output_line?: string | null; line?: number },
  speech: string,
  code: string,
): number {
  const blob = tokenizeSpeech(speech);
  if (!blob.length) return 0;
  const hay = new Set(blob);
  let score = 0;
  const output = String(step.output_line || "")
    .trim()
    .toLowerCase()
    .replace(/^["']|["']$/g, "");
  if (output) {
    if (hay.has(output) || speech.toLowerCase().includes(output)) score += 24;
    if (output === "true" && hay.has("true")) score += 8;
    if (output === "false" && hay.has("false")) score += 8;
  }
  for (const word of tokenizeSpeech(`${step.description || ""} ${step.label || ""}`)) {
    if (word.length > 3 && hay.has(word)) score += 2;
  }
  const line = (code || "").replace(/\n$/, "").split("\n")[Math.max(0, (step.line || 1) - 1)] || "";
  for (const id of line.match(/[A-Za-z_][A-Za-z0-9_]{1,}/g) || []) {
    if (id.length > 2 && hay.has(id.toLowerCase())) score += 5;
  }
  return score;
}

function matchStepsToCues(
  steps: { description?: string; label?: string; output_line?: string | null; line?: number }[],
  cues: SyncCue[],
  code: string,
): Array<number | undefined> {
  const assigned: Array<number | undefined> = cues.map(() => undefined);
  if (!steps.length || !cues.length) return assigned;
  const used = new Set<number>();
  cues.forEach((cue, cueIndex) => {
    let best = -1;
    let bestScore = 0;
    steps.forEach((step, stepIndex) => {
      if (used.has(stepIndex)) return;
      const score = stepSpeechScore(step, cue.text, code);
      if (score > bestScore) {
        bestScore = score;
        best = stepIndex;
      }
    });
    if (best >= 0 && bestScore >= 5) {
      assigned[cueIndex] = best;
      used.add(best);
    }
  });
  let last: number | undefined;
  for (let index = 0; index < cues.length; index += 1) {
    if (typeof assigned[index] === "number") {
      last = assigned[index];
    } else {
      assigned[index] = last;
    }
  }
  return assigned;
}

export function cueAt(cues: SyncCue[], time: number): SyncCue | null {
  if (!cues.length) return null;
  const hit = cues.find((cue) => time >= cue.start && time < cue.end);
  if (hit) return hit;
  if (time >= cues[cues.length - 1].end) return cues[cues.length - 1];
  return cues[0];
}
