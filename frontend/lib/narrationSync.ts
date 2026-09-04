import { highlightForSpeech } from "@/lib/codeFocus";
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

function sceneHighlight(scene: LessonScene, speech?: string | null, key?: string | null): HighlightRange | null {
  if (scene.type !== "code" && scene.type !== "execution") return null;
  const code = scene.code || "";
  const ranges = scene.highlight_ranges ?? [];
  const spoken = [key, speech].filter(Boolean).join(" ");
  return highlightForSpeech(code, ranges, spoken);
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
      highlight: highlightForSpeech(code, scene.highlight_ranges ?? [], step.description) || {
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
      highlight: sceneHighlight(scene, segment.text, segment.highlight),
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
        highlight: sceneHighlight(scene, scene.narration || ""),
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
    return {
      start,
      end: index === sentences.length - 1 ? duration + 0.05 : cursor,
      text,
      highlight: sceneHighlight(scene, text),
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
