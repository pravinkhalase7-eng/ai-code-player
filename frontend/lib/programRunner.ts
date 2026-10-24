import type { HighlightRange, Lesson } from "@/types/lesson";

export function isProgramRunnerLesson(lesson: Lesson | null | undefined): boolean {
  return (lesson?.reel_mode || "").trim().toLowerCase() === "runner";
}

/** Reveal the snippet as if it is being typed, finishing just before the scene ends. */
export function typedCode(code: string, currentTime: number, duration: number): string {
  const src = code || "";
  if (!src) return "";
  const span = Math.max(0.35, duration * 0.9);
  const progress = Math.min(1, Math.max(0, currentTime / span));
  const n = Math.max(0, Math.min(src.length, Math.floor(progress * src.length)));
  return src.slice(0, n);
}

export function typingCaretHighlight(revealed: string): HighlightRange | null {
  if (!revealed) return { start_line: 1, end_line: 1, start_col: 0, label: "typing" };
  const line = revealed.split("\n").length;
  return { start_line: line, end_line: line, start_col: 0, label: "typing" };
}
