import type { Lesson } from "../../types/lesson";

export const FPS = 30;
export const COMPOSITION_ID = "LessonComposition";

export type AspectRatio = "16:9" | "9:16";

export function compositionSize(aspect: AspectRatio): { width: number; height: number } {
  return aspect === "9:16" ? { width: 1080, height: 1920 } : { width: 1920, height: 1080 };
}

export function sceneFrames(duration: number): number {
  return Math.max(1, Math.round(duration * FPS));
}

export function totalFrames(lesson: Lesson): number {
  return lesson.scenes.reduce((sum, scene) => sum + sceneFrames(scene.duration), 0);
}
