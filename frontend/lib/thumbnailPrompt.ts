import type { Lesson } from "@/types/lesson";

/**
 * Exact Gemini image prompt used when image_provider=gemini generated reel posters
 * (before SVG fallback). Matches backend thumbnail_prompt + GeminiImage style wrapper.
 */
export function buildThumbnailPrompt(lesson: Lesson, seed = 42): string {
  const topic = (lesson.topic || lesson.title || "Coding short").trim();
  const language = (lesson.language || "java").trim();
  const core =
    `Vertical 9:16 cinematic social-media thumbnail for a coding reel. ` +
    `Topic: ${topic}. Language: ${language}. ` +
    `Dark glossy background, neon amber and cyan light, huge readable title '${topic}', ` +
    `small badge 'BYTE', abstract code rain, no watermarks, no celebrity faces, ` +
    `high contrast, catchy, viral educational poster.`;

  // Same prefix GeminiImage.generate used: "{style} educational illustration, aspect …"
  return (
    `cinematic viral educational poster educational illustration, aspect 9:16, seed ${seed}. ` +
    core
  );
}
