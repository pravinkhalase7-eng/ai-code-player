import type { HighlightRange, Lesson, LessonScene } from "@/types/lesson";
import type { ReelBeat } from "@/lib/reelDebugSync";
import { splitSentences } from "@/lib/narrationSync";

export type ReelHeadline = {
  kicker: string;
  title: string;
  snippet?: string;
  key: string;
};

export type SpokenWord = {
  text: string;
  start: number;
  end: number;
  active: boolean;
  spoken: boolean;
};

const DURATION_NOISE = /\b(?:in\s+)?30(?:\s*|-)?seconds?\b|\b30s\b/gi;

export function stripDurationNoise(text: string): string {
  const stripped = (text || "")
    .replace(DURATION_NOISE, " ")
    .replace(/^\s*[:\-–—]\s*/, "")
    .replace(/\s+([,.!?;:।])/g, "$1")
    .replace(/\s{2,}/g, " ")
    .trim();
  if (!stripped) return "";
  return stripped.charAt(0).toUpperCase() + stripped.slice(1);
}

export function displayTopic(topic: string): string {
  return stripDurationNoise(topic) || topic;
}

function pretty(label: string): string {
  const cleaned = stripDurationNoise(label).replace(/[_-]+/g, " ").replace(/\s+/g, " ").trim();
  if (!cleaned) return "";
  if (!/[A-Za-z]/.test(cleaned)) return cleaned;
  return cleaned.replace(/\b[a-zA-Z]/g, (char) => char.toUpperCase());
}

export function highlightedSnippet(code: string, highlight: HighlightRange | null): string {
  if (!highlight) return "";
  const lines = (code || "").replace(/\n$/, "").split("\n");
  const start = Math.max(0, highlight.start_line - 1);
  const end = Math.max(start, (highlight.end_line || highlight.start_line) - 1);
  return lines
    .slice(start, end + 1)
    .map((line) => line.trim())
    .filter(Boolean)
    .join(" ")
    .slice(0, 88);
}

export function timedWords(text: string, start: number, end: number, time: number): SpokenWord[] {
  const words = (text || "").trim().split(/\s+/).filter(Boolean);
  if (!words.length) return [];
  const span = Math.max(0.08, end - start);
  const weights = words.map((word) => Math.max(2, word.replace(/[^\w\u0900-\u0D7F]/g, "").length) + 0.35);
  const total = weights.reduce((sum, weight) => sum + weight, 0) || 1;
  let cursor = start;
  return words.map((word, index) => {
    const duration = span * (weights[index] / total);
    const wordStart = cursor;
    const wordEnd = index === words.length - 1 ? end : cursor + duration;
    cursor = wordEnd;
    return {
      text: word,
      start: wordStart,
      end: wordEnd,
      active: time >= wordStart && time < wordEnd,
      spoken: time >= wordStart,
    };
  });
}

export function spokenPhraseAt(
  narration: string,
  time: number,
  duration: number,
): { text: string; raw: string; start: number; end: number } {
  const sentences = splitSentences(narration || "").filter(Boolean);
  const span = Math.max(duration, 0.4);
  if (!sentences.length) {
    const raw = (narration || "").replace(/\s+/g, " ").trim();
    return { text: stripDurationNoise(raw), raw, start: 0, end: span };
  }
  const weights = sentences.map((sentence) => Math.max(1, sentence.split(/\s+/).length));
  const total = weights.reduce((sum, value) => sum + value, 0);
  const t = Math.min(Math.max(0, time), span);
  let cursor = 0;
  for (let index = 0; index < sentences.length; index += 1) {
    const length = span * (weights[index] / total);
    const start = cursor;
    const end = index === sentences.length - 1 ? span + 0.04 : cursor + length;
    if (t < end) {
      const raw = sentences[index];
      return { text: stripDurationNoise(raw), raw, start, end };
    }
    cursor = end;
  }
  const raw = sentences[sentences.length - 1];
  return { text: stripDurationNoise(raw), raw, start: 0, end: span };
}

function tokenKey(word: string): string {
  return word.replace(/[^\w]/g, "").toLowerCase();
}

export function visibleKaraokeWords(words: SpokenWord[]): SpokenWord[] {
  return words.filter((word, index) => {
    const current = tokenKey(word.text);
    const prev = index > 0 ? tokenKey(words[index - 1].text) : "";
    const next = index < words.length - 1 ? tokenKey(words[index + 1].text) : "";
    if (current === "30" || current === "30s") return false;
    if ((current === "second" || current === "seconds") && (prev === "30" || prev === "30s")) return false;
    if (current === "in" && (next === "30" || next === "30s")) return false;
    return true;
  });
}

export function reelHeadline(
  lesson: Lesson,
  scene: LessonScene,
  highlight: HighlightRange | null,
  _beat: ReelBeat | null,
  code = "",
  caption = "",
): ReelHeadline {
  const snippet = highlightedSnippet(code, highlight);
  const spoken = stripDurationNoise(caption);
  let kicker = "";
  if (scene.type === "execution" || scene.type === "terminal") {
    kicker = "Output";
  } else if (scene.type === "summary") {
    kicker = "Remember";
  } else if (scene.type === "intro") {
    kicker = "";
  } else if (highlight?.label) {
    kicker = pretty(highlight.label);
  } else if (scene.type === "code") {
    kicker = "This line";
  }

  const title = spoken || snippet || pretty(displayTopic(lesson.topic));
  const snippetKey = snippet.slice(0, 24).toLowerCase();
  const showSnippet = Boolean(snippet && snippetKey && !spoken.toLowerCase().includes(snippetKey));

  return {
    kicker,
    title,
    snippet: showSnippet ? snippet : undefined,
    key: `${scene.id}-${title}`,
  };
}
