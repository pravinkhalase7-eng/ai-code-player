import type { Lesson } from "@/types/lesson";

/**
 * High-CTR viral Shorts poster prompt (matches backend thumbnail_prompt).
 * Used when copying a Gemini-style prompt from the player.
 */
export function buildThumbnailPrompt(lesson: Lesson, seed = 42): string {
  const topic = (lesson.topic || lesson.title || "Coding short").trim();
  const language = (lesson.language || "java").trim();
  const spoken = (lesson.spoken_language || "en").trim().toLowerCase();
  const mode = (lesson.reel_mode || "").trim().toLowerCase();
  const hindi = spoken === "hi" || spoken.startsWith("hi") || spoken === "hindi";

  const words = topic.match(/[A-Za-z0-9+#]+/g) || [];
  let headline =
    words
      .slice(0, 4)
      .map((w) => w.toUpperCase())
      .join(" ") || language.toUpperCase();
  if (headline.length > 28) headline = `${headline.slice(0, 28).trimEnd()}…`;

  const hooks = hindi
    ? ["कौन सा?", "वाह!", "रुको!", "ये कैसे?", "सच??"]
    : ["WHICH ONE?", "WAIT…", "MOST MISS THIS", "THIS OR THAT?", "WHY?"];
  const hook = hooks[Math.abs(seed) % hooks.length];

  const blob = topic.toLowerCase();
  let visual: string;
  if (/hash\s*map|hashtable/.test(blob) && !blob.includes("collection")) {
    visual =
      "glowing HashMap whiteboard: buckets, chained nodes, hash→index motion, neon collision energy";
  } else if (/garbage|\bgc\b|heap/.test(blob)) {
    visual =
      "glowing GC heap with live vs dead objects, mark & sweep beams, futuristic memory cleanup";
  } else if (/collection|arraylist|hashset|\bqueue\b|array\s*list/.test(blob)) {
    visual =
      "glowing Java logo upper-middle; large floating cards ArrayList, HashSet, HashMap, Queue; glowing data flowing between them";
  } else if (/concurren|multithread|\bthreads?\b|synchronized|completable\s*future|\blocks?\b/.test(blob)) {
    visual =
      "glowing Java logo upper-middle; floating neon cards Thread, synchronized, Lock, CompletableFuture; parallel work lanes merging into shared data";
  } else {
    visual = `futuristic ${language} scene with glowing emblem upper-middle; neon concept cards naming the real subtopics; light trails`;
  }

  const explain =
    mode === "explainer" || mode === "info" ? "how-it-works explainer" : "coding short";

  return (
    `Create a highly catchy, high-CTR vertical 9:16 thumbnail/poster for a programming video. ` +
    `Topic: ${topic}. Language: ${language}. Format: ${explain}. ` +
    `Main headline in huge bold typography: "${headline}". ` +
    `Curiosity hook in a smaller highly contrasting text box: "${hook}". ` +
    `Visual: ${visual}. ` +
    `Composition: logo/main visual upper-middle; headline near center huge bold; curiosity hook in contrasting box; ` +
    `keep text off extreme edges; mobile-clear; strong vertical flow; clean uncluttered. ` +
    `Colors: dark black/navy with Java red, orange, electric blue, purple neon; glow, depth, shadows. ` +
    `Style: viral coding thumbnail, premium YouTube Shorts, futuristic, cinematic lighting, bold 3D type, ` +
    `neon glow, high contrast, sharp, dynamic, professional, striking. ` +
    `Communicate "${topic} made simple" instantly while creating curiosity. ` +
    `Aspect 9:16, 1080×1920, mobile-first. No watermark, no clutter. seed ${seed}.`
  );
}
