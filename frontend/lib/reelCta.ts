import type { Lesson, LessonScene } from "@/types/lesson";
import { displayTopic } from "@/lib/reelHeadlines";

export const REEL_HANDLE = "@byte.codes";

export function isPosterScene(type: string | undefined): boolean {
  return type === "intro" || type === "summary";
}

export function commentPrompt(topic: string): string {
  const text = (topic || "").toLowerCase();
  if (/(callback|promise|async)/.test(text)) return "Comment: callback, promise, or async?";
  if (/\bloop/.test(text)) return "Comment: for or while?";
  if (/stream/.test(text)) return "Comment: stream or loop?";
  const short = topic.split(/\s+/).slice(0, 4).join(" ");
  return short ? `Comment your ${short} take` : "Comment if this helped";
}

export function reelCta(lesson: Lesson, scene?: LessonScene) {
  const topic = displayTopic(lesson.topic);
  const takeaway = scene?.takeaways?.[0] || "";
  return {
    handle: REEL_HANDLE,
    follow: "Follow",
    save: "Save",
    comment: commentPrompt(topic),
    endLine: takeaway || `Save this ${topic} trick`,
    endAction: "Follow Byte for daily shorts",
  };
}
