import type { Lesson, LessonScene } from "@/types/lesson";

export const QUIZ_COUNTDOWN_SECONDS = 5;
export const QUIZ_LETTERS = ["A", "B", "C", "D"] as const;

export type TrickyQuizPhase = "prompt" | "countdown" | "reveal";

export type TrickyQuizState = {
  phase: TrickyQuizPhase;
  count: number;
  ring: number;
  quiz: LessonScene;
  code: string;
  options: string[];
  answerIndex: number;
  question: string;
  explanation: string;
};

export function isTrickyQuizLesson(lesson: Lesson | null | undefined): boolean {
  return (lesson?.reel_mode || "").trim().toLowerCase() === "quiz";
}

export function quizSceneFromLesson(lesson: Lesson): LessonScene | null {
  return (
    lesson.scenes.find((scene) => scene.type === "quiz") ||
    lesson.scenes.find((scene) => (scene.options || []).length >= 2) ||
    null
  );
}

export function quizHoldSeconds(scene: LessonScene | undefined): number {
  const duration = Number(scene?.duration || 0);
  return Math.max(duration, QUIZ_COUNTDOWN_SECONDS + 2.4);
}

export function trickyQuizState(
  lesson: Lesson,
  scene: LessonScene,
  currentTime: number,
  duration: number,
): TrickyQuizState | null {
  const quiz = quizSceneFromLesson(lesson);
  if (!quiz) return null;
  const options = (quiz.options || []).slice(0, 4);
  const answerIndex =
    typeof quiz.answer === "number" && quiz.answer >= 0 && quiz.answer < options.length ? quiz.answer : 0;
  const code = (quiz.code || scene.code || "").trim();
  const question = (quiz.question || "What does this print?").trim();
  const explanation = (quiz.explanation || scene.narration || "").trim();
  const base = {
    quiz,
    code,
    options,
    answerIndex,
    question,
    explanation,
  };

  if (scene.type === "summary") {
    return { ...base, phase: "reveal", count: 0, ring: 0 };
  }
  if (scene.type !== "quiz") {
    return { ...base, phase: "prompt", count: QUIZ_COUNTDOWN_SECONDS, ring: 1 };
  }

  const window = Math.max(duration, quizHoldSeconds(scene));
  const think = Math.max(0.8, window - QUIZ_COUNTDOWN_SECONDS);
  if (currentTime < think) {
    return { ...base, phase: "prompt", count: QUIZ_COUNTDOWN_SECONDS, ring: 1 };
  }
  const remain = Math.max(0, QUIZ_COUNTDOWN_SECONDS - (currentTime - think));
  if (remain <= 0.05) {
    return { ...base, phase: "reveal", count: 0, ring: 0 };
  }
  return {
    ...base,
    phase: "countdown",
    count: Math.max(1, Math.ceil(remain)),
    ring: Math.max(0, Math.min(1, remain / QUIZ_COUNTDOWN_SECONDS)),
  };
}
