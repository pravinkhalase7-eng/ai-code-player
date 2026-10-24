import { cueAt, type SyncCue } from "@/lib/narrationSync";
import type { HighlightRange, Lesson } from "@/types/lesson";

export function isProgramRunnerLesson(lesson: Lesson | null | undefined): boolean {
  return (lesson?.reel_mode || "").trim().toLowerCase() === "runner";
}

/** Reveal the snippet with the spoken cue: earlier lines stay, the current line types with the words. */
export function typedCode(
  code: string,
  currentTime: number,
  duration: number,
  cues?: SyncCue[] | null,
): string {
  const src = code || "";
  if (!src) return "";
  const lines = src.replace(/\n$/, "").split("\n");
  const start = cues?.[0]?.start ?? 0;
  const end = cues?.length ? cues[cues.length - 1].end : duration;
  const span = Math.max(0.2, end - start);
  const progress = Math.min(1, Math.max(0, (currentTime - start) / span));
  if (!cues?.length || cues.length < 2) {
    return src.slice(0, Math.floor(progress * src.length));
  }
  const targetAt = (index: number) => {
    const cue = cues[index];
    const highlighted = cue.highlight?.end_line || cue.highlight?.start_line;
    if (highlighted) return Math.min(lines.length, Math.max(1, highlighted));
    return Math.max(1, Math.round(((index + 1) / cues.length) * lines.length));
  };
  const cue = cueAt(cues, currentTime) || cues[0];
  const index = Math.max(0, cues.indexOf(cue));
  let revealed = 0;
  for (let cursor = 0; cursor < index; cursor += 1) revealed = Math.max(revealed, targetAt(cursor));
  const target = Math.max(revealed, targetAt(index));
  const local = Math.min(1, Math.max(0, (currentTime - cue.start) / Math.max(0.05, cue.end - cue.start)));
  const before = lines.slice(0, revealed).join("\n");
  const chunk = lines.slice(revealed, target).join("\n");
  const partial = chunk.slice(0, Math.floor(local * chunk.length));
  if (!before) return partial;
  if (!partial) return before;
  return `${before}\n${partial}`;
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
