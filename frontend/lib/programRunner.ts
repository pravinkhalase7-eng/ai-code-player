import type { Lesson } from "@/types/lesson";

export function isProgramRunnerLesson(lesson: Lesson | null | undefined): boolean {
  return (lesson?.reel_mode || "").trim().toLowerCase() === "runner";
}
