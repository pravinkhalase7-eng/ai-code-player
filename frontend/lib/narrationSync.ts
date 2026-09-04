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
    .split(/(?<=[.!?])\s+|\n+/)
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

function findHighlight(ranges: HighlightRange[], key?: string | null): HighlightRange | null {
  if (!key || !ranges.length) return null;
  const needle = key.toLowerCase();
  return (
    ranges.find((item) => item.label.toLowerCase() === needle) ||
    ranges.find((item) => needle.includes(item.label.toLowerCase()) || item.label.toLowerCase().includes(needle)) ||
    ranges.find((item) =>
      item.label
        .toLowerCase()
        .split(/\W+/)
        .filter((word) => word.length > 3)
        .some((word) => needle.includes(word)),
    ) ||
    null
  );
}

export function buildCues(scene: LessonScene, audioDuration?: number): SyncCue[] {
  const duration = clipDuration(scene, audioDuration);
  const highlights = scene.highlight_ranges ?? [];

  if (scene.type === "execution" && scene.iterations?.length) {
    const slice = duration / scene.iterations.length;
    return scene.iterations.map((step, index) => ({
      start: index * slice,
      end: (index + 1) * slice,
      text: step.description,
      highlight: {
        start_line: step.line,
        end_line: step.line,
        start_col: 0,
        label: step.label || "step",
      },
      stepIndex: index,
    }));
  }

  const segments = scene.segments ?? [];
  if (segments.length >= 1) {
    const last = Math.max(...segments.map((segment) => segment.end), 0.1);
    const scale = duration / last;
    return segments.map((segment) => ({
      start: segment.start * scale,
      end: segment.end * scale,
      text: segment.text,
      highlight: findHighlight(highlights, segment.highlight) || findHighlight(highlights, segment.text),
      expression: segment.expression,
    }));
  }

  const sentences = splitSentences(scene.narration || "");
  if (!sentences.length) {
    return [
      {
        start: 0,
        end: duration,
        text: scene.narration || "",
        highlight: highlights[0] ?? null,
      },
    ];
  }

  const weights = sentences.map((sentence) => Math.max(1, sentence.split(/\s+/).length));
  const total = weights.reduce((sum, value) => sum + value, 0);
  let cursor = 0;
  return sentences.map((text, index) => {
    const span = duration * (weights[index] / total);
    const start = cursor;
    cursor += span;
    const matched = findHighlight(highlights, text);
    const sequential =
      scene.type === "code" && highlights.length
        ? highlights[Math.min(index, highlights.length - 1)]
        : null;
    return {
      start,
      end: index === sentences.length - 1 ? duration + 0.05 : cursor,
      text,
      highlight: matched || sequential,
    };
  });
}

export function cueAt(cues: SyncCue[], time: number): SyncCue | null {
  if (!cues.length) return null;
  const hit = cues.find((cue) => time >= cue.start && time < cue.end);
  if (hit) return hit;
  if (time >= cues[cues.length - 1].end) return cues[cues.length - 1];
  return cues[0];
}
