import { API_BASE } from "@/lib/utils";
import type { Lesson, LessonSummary } from "@/types/lesson";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    });
  } catch {
    throw new Error("Could not reach the tutor API. Make sure it is running on port 8010.");
  }
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = body.detail;
    const message =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((item: { msg?: string }) => item.msg).filter(Boolean).join(" ")
          : body.error || response.statusText || "Request failed";
    throw new Error(message);
  }
  return body as T;
}

export function createLesson(
  topic: string,
  language = "java",
  level = "beginner",
  format: "lesson" | "reel" = "lesson",
  spokenLanguage = "en",
  reelSeconds = 30,
  requiresCode?: boolean,
) {
  return request<{ lesson_id: string; status: string; job_id: string }>(
    "/api/v1/tutor/lesson",
    {
      method: "POST",
      body: JSON.stringify({
        topic,
        language,
        level,
        format,
        spoken_language: spokenLanguage,
        reel_seconds: format === "reel" ? reelSeconds : 30,
        ...(typeof requiresCode === "boolean" ? { requires_code: requiresCode } : {}),
      }),
    },
  );
}

export function getLesson(lessonId: string) {
  return request<{ lesson: Lesson; status: string; warnings: string[] }>(
    `/api/v1/lesson/${lessonId}`,
  );
}

export function listLessons() {
  return request<{ lessons: LessonSummary[] }>("/api/v1/lessons");
}

export function executeCode(language: string, code: string, lessonId?: string) {
  return request<{
    success: boolean;
    stdout: string[];
    stderr: string;
    execution_time_ms: number;
    timed_out: boolean;
    compile_error: boolean;
    iterations?: {
      index: number;
      label: string;
      description: string;
      line: number;
      condition?: string | null;
      condition_result?: boolean | null;
      output_line?: string | null;
      variables: { name: string; value: string; type?: string }[];
      stopped?: boolean;
    }[];
  }>("/api/v1/code/execute", {
    method: "POST",
    body: JSON.stringify({ language, code, lesson_id: lessonId }),
  });
}

export function explainRunError(payload: {
  language: string;
  code: string;
  stderr: string;
  compile_error: boolean;
  timed_out: boolean;
  lesson_id?: string;
}) {
  return request<{
    issue: string;
    explanation: string;
    line: number | null;
    label: string;
    suggested_code: string | null;
  }>("/api/v1/code/run-help", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function sendChat(lessonId: string, message: string) {
  return request<{
    reply: string;
    expression: string;
    execution: { stdout: string[]; stderr: string; timed_out: boolean; success: boolean } | null;
  }>("/api/v1/tutor/chat", {
    method: "POST",
    body: JSON.stringify({ lesson_id: lessonId, message }),
  });
}

export function answerQuiz(questionId: string, answer: number | string | null, code?: string) {
  return request<{
    evaluation: {
      status: "correct" | "partially_correct" | "incorrect";
      misconception: string | null;
      explanation: string;
      next_action: string;
    };
    mastery: number | null;
  }>(`/api/v1/quiz/${questionId}/answer`, {
    method: "POST",
    body: JSON.stringify({ answer, code }),
  });
}

export function getProgress(lessonId: string) {
  return request<{
    lesson_id: string;
    current_scene: string | null;
    completion_percent: number;
    score: number;
    scene_index: number;
    time_spent_ms: number;
  }>(`/api/v1/lesson/${lessonId}/progress`);
}

export function saveProgress(
  lessonId: string,
  payload: { current_scene?: string; scene_index: number; completion_percent: number; time_spent_ms: number },
) {
  return request(`/api/v1/lesson/${lessonId}/progress`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getHealth() {
  return request<{
    status: string;
    gemini_configured: boolean;
    gemini_model: string;
    tts_provider: string;
    google_tts_configured?: boolean;
    code_runner: string;
    missing_keys: string[];
  }>("/api/v1/health");
}

export function generateThumbnail(lessonId: string) {
  return request<{ lesson: Lesson; status: string; warnings: string[] }>(
    `/api/v1/lesson/${lessonId}/thumbnail`,
    { method: "POST" },
  );
}

export function saveReelScript(
  lessonId: string,
  payload: {
    code?: string;
    scenes: { id: string; narration: string; takeaways?: string[] }[];
    rewrite?: boolean;
  },
) {
  return request<{ lesson: Lesson; status: string; warnings: string[] }>(
    `/api/v1/lesson/${lessonId}/script`,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function startRender(lessonId: string) {
  return request<{ job_id: string; status: string }>(`/api/v1/lesson/${lessonId}/render`, {
    method: "POST",
  });
}
