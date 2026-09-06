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
    const slice = duration / scene.iterations.length;
    return scene.iterations.map((step, index) => ({
      start: index * slice,
      end: (index + 1) * slice,
      text: step.description,
      highlight:
        progressiveHighlight(code, scene.highlight_ranges ?? [], step.description, index, scene.iterations!.length) || {
          start_line: step.line || 1,
          end_line: step.line || 1,
          start_col: 0,
          label: step.label || "step",
        },
      stepIndex: index,
    }));
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

export function cueAt(cues: SyncCue[], time: number): SyncCue | null {
  if (!cues.length) return null;
  const hit = cues.find((cue) => time >= cue.start && time < cue.end);
  if (hit) return hit;
  if (time >= cues[cues.length - 1].end) return cues[cues.length - 1];
  return cues[0];
}
