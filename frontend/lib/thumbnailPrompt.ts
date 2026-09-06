import type { Lesson } from "@/types/lesson";

const ACCENTS: Record<string, string> = {
  java: "#fb923c (warm orange)",
  python: "#38bdf8 (sky blue)",
  javascript: "#facc15 (bright yellow)",
  js: "#facc15 (bright yellow)",
};

function heroCodeLine(lesson: Lesson): string | null {
  for (const scene of lesson.scenes) {
    const code = (scene.code || "").trim();
    if (!code) continue;
    const line =
      code
        .split("\n")
        .map((item) => item.trim())
        .find((item) => item && !item.startsWith("//") && !item.startsWith("#") && item !== "{" && item !== "}") ||
      null;
    if (line) return line.slice(0, 72);
  }
  return null;
}

function conceptKeywords(lesson: Lesson): string {
  const parts = [
    ...(lesson.concepts || []),
    ...(lesson.objectives || []).slice(0, 3),
  ]
    .map((item) => item.trim())
    .filter(Boolean);
  if (parts.length) return parts.slice(0, 5).join(", ");
  return lesson.topic;
}

/**
 * Ready-to-paste Gemini image prompt for a 9:16 TECHSHALA reel poster.
 */
export function buildThumbnailPrompt(lesson: Lesson): string {
  const lang = (lesson.language || "java").toLowerCase();
  const accent = ACCENTS[lang] || "#a78bfa (soft violet)";
  const mode =
    lesson.requires_code === false ||
    !lesson.scenes.some((scene) => scene.type === "code" || scene.type === "execution")
      ? "INFO"
      : "CODE";
  const spoken = (lesson.spoken_language || "en").toUpperCase();
  const hero = mode === "CODE" ? heroCodeLine(lesson) : null;
  const focus =
    mode === "CODE" && hero
      ? `Show ONE hero code line as large monospace text: "${hero}". Keep it legible; no dense wall of code.`
      : `Show 3–5 crisp concept keywords as bold labels: ${conceptKeywords(lesson)}. No fake code stubs.`;

  return [
    "Create a clean vertical 9:16 (1080x1920) Instagram Reels / YouTube Shorts poster for TECHSHALA, an AI coding tutor brand.",
    `Topic: ${lesson.topic}`,
    `Programming language badge: ${lang.toUpperCase()}`,
    `Spoken language context: ${spoken}`,
    `Mode: ${mode} ${mode === "CODE" ? "(code walkthrough short)" : "(concept / explain short — no program)"}`,
    "",
    "Brand & style:",
    "- Deep dark background with subtle gradient and soft glow orbs",
    "- Top-left or top-center TECHSHALA badge / wordmark only (no other watermarks or logos)",
    `- Accent color for highlights and glow: ${accent}`,
    "- High contrast, modern tech aesthetic, educational flat + soft neon",
    "- Plenty of safe margins for mobile crop",
    "",
    "Layout:",
    `- Large bold title centered upper-middle: "${lesson.topic}"`,
    "- Small language chip near the badge",
    focus,
    "- Bottom handle hint: @techshalabypavi and tiny 'AI CODING TUTOR' label",
    "",
    "Hard rules:",
    "- Vertical poster only, no horizontal letterboxing",
    "- No watermarks except the TECHSHALA mark",
    "- No cluttered UI chrome, no fake phone frames, no stock people photos",
    "- Text must stay sharp and readable at phone size",
  ].join("\n");
}
