export type KaraokeWord = {
  text: string;
  start: number;
  end: number;
  index: number;
};

type SegmentLike = { text?: string; start: number; end: number };

function splitWords(text: string): string[] {
  return (text || "")
    .trim()
    .split(/\s+/)
    .filter(Boolean);
}

/** Spread words across [start, end] with light length weighting (speech-ish). */
export function wordsForSpan(text: string, start: number, end: number, indexOffset = 0): KaraokeWord[] {
  const words = splitWords(text);
  if (!words.length) return [];
  const span = Math.max(0.12, end - start);
  const weights = words.map((word) => Math.max(1, word.replace(/[^a-zA-Z0-9\u0900-\u097F]+/g, "").length || 1));
  const total = weights.reduce((sum, value) => sum + value, 0);
  let cursor = start;
  return words.map((word, index) => {
    // Slightly longer on early words — TTS often rushes the tail.
    const bias = 1 + Math.max(0, (words.length - index) / words.length) * 0.15;
    const slice = span * ((weights[index] * bias) / (total * 1.075));
    const wordStart = cursor;
    cursor += slice;
    return {
      text: word,
      start: wordStart,
      end: index === words.length - 1 ? end : cursor,
      index: indexOffset + index,
    };
  });
}

/**
 * Build karaoke words for the CURRENT cue only.
 * Pass cueStart/cueEnd from cueAt(buildCues(...)) so highlight tracks the spoken line.
 */
export function buildKaraokeWords(
  text: string,
  duration: number,
  opts?: {
    cueStart?: number;
    cueEnd?: number;
    segments?: SegmentLike[] | null;
  },
): KaraokeWord[] {
  const safeDuration = Math.max(0.2, duration || 0.2);
  const cueStart = Math.max(0, opts?.cueStart ?? 0);
  let cueEnd = opts?.cueEnd ?? safeDuration;
  if (!(cueEnd > cueStart)) cueEnd = Math.min(safeDuration, cueStart + 0.8);

  const cleaned = (text || "").trim();
  if (!cleaned) return [];

  // If a single narration segment covers this cue text, prefer its scaled bounds.
  const segs = (opts?.segments || []).filter((item) => (item.text || "").trim());
  if (segs.length) {
    const last = Math.max(...segs.map((item) => Number(item.end) || 0), 0.1);
    const scale = safeDuration / last;
    const norm = cleaned.toLowerCase().replace(/\s+/g, " ");
    const hit = segs.find((seg) => {
      const segText = String(seg.text || "")
        .trim()
        .toLowerCase()
        .replace(/\s+/g, " ");
      return segText === norm || segText.includes(norm) || norm.includes(segText);
    });
    if (hit) {
      const start = Math.max(0, (Number(hit.start) || 0) * scale);
      const end = Math.max(start + 0.12, (Number(hit.end) || start + 0.5) * scale);
      // If cue is a sentence inside a longer segment, keep cueStart/cueEnd when provided
      // and tighter than the segment (sentence-level cues from buildCues).
      if (opts?.cueStart != null && opts?.cueEnd != null && opts.cueEnd - opts.cueStart < end - start) {
        return wordsForSpan(cleaned, cueStart, cueEnd);
      }
      return wordsForSpan(cleaned, start, end);
    }
  }

  return wordsForSpan(cleaned, cueStart, cueEnd);
}

export function activeWordIndex(words: KaraokeWord[], time: number): number {
  if (!words.length) return -1;
  if (time < words[0].start) return 0;
  const hit = words.findIndex((word) => time >= word.start && time < word.end);
  if (hit >= 0) return hit;
  if (time >= words[words.length - 1].end) return words.length - 1;
  // Between gaps — pick nearest prior word
  for (let i = words.length - 1; i >= 0; i -= 1) {
    if (time >= words[i].start) return i;
  }
  return 0;
}

/** Keep a readable window centered on the spoken word. */
export function karaokeWindow(words: KaraokeWord[], active: number, maxWords = 12): KaraokeWord[] {
  if (!words.length) return [];
  if (words.length <= maxWords) return words;
  const half = Math.floor(maxWords / 2);
  let start = Math.max(0, active - half);
  let end = Math.min(words.length, start + maxWords);
  start = Math.max(0, end - maxWords);
  return words.slice(start, end);
}
