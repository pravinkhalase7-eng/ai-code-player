import type { SyncCue } from "@/lib/narrationSync";
import type { HighlightRange, Lesson } from "@/types/lesson";

export function isProgramRunnerLesson(lesson: Lesson | null | undefined): boolean {
  return (lesson?.reel_mode || "").trim().toLowerCase() === "runner";
}

/** Reveal the snippet across the spoken window so typing does not outrun the voiceover. */
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
  const progress = Math.min(1, Math.max(0, (currentTime - start) / span));
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
