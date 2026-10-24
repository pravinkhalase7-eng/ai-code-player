import { activeWordIndex, wordsForSpan } from "@/lib/karaokeCaption";
import type { SyncCue } from "@/lib/narrationSync";
import type { HighlightRange, Lesson } from "@/types/lesson";

/** Chirp leads estimated clocks; type slightly early so characters land with the words. */
const TYPING_LEAD = 0.16;

export function isProgramRunnerLesson(lesson: Lesson | null | undefined): boolean {
  return (lesson?.reel_mode || "").trim().toLowerCase() === "runner";
}

/** Reveal characters in lockstep with spoken words, not a separate visual timer. */
export function typedCode(
  code: string,
  currentTime: number,
  duration: number,
  cues?: SyncCue[] | null,
): string {
  const src = code || "";
  if (!src) return "";
  const start = cues?.[0]?.start ?? 0;
  const end = cues?.length ? cues[cues.length - 1].end : duration;
  const span = Math.max(0.2, end - start);
  const t = currentTime + TYPING_LEAD;
  const spoken = (cues || []).map((cue) => cue.text).filter(Boolean).join(" ").trim();
  const words = spoken ? wordsForSpan(spoken, start, end) : [];
  let progress = (t - start) / span;
  if (words.length) {
    const index = Math.max(0, activeWordIndex(words, t));
    const word = words[index];
    const local = Math.min(1, Math.max(0, (t - word.start) / Math.max(0.04, word.end - word.start)));
    progress = (index + local) / words.length;
  }
  progress = Math.min(1, Math.max(0, progress));
  return src.slice(0, Math.floor(progress * src.length));
}

export function typingCaretHighlight(revealed: string): HighlightRange | null {
  if (!revealed) return { start_line: 1, end_line: 1, start_col: 0, label: "typing" };
  const line = revealed.split("\n").length;
  return { start_line: line, end_line: line, start_col: 0, label: "typing" };
}

export type ResultChip = { line: number; text: string; kind: "ok" | "bad" | "out" };

export function resultKind(text: string): ResultChip["kind"] {
  const t = String(text || "").trim().toLowerCase();
  if (t === "true" || t === "yes") return "ok";
  if (t === "false" || t === "no") return "bad";
  return "out";
}

export function formatResultChip(text: string): string {
  const raw = String(text || "").trim();
  const kind = resultKind(raw);
  if (kind === "ok") return `✅ ${raw || "True"}`;
  if (kind === "bad") return `❌ ${raw || "False"}`;
  return raw;
}

export function printLineNumbers(code: string): number[] {
  return (code || "")
    .split("\n")
    .flatMap((line, index) =>
      /\b(print|println|console\.log|System\.out)\s*\(/.test(line) ? [index + 1] : [],
    );
}
