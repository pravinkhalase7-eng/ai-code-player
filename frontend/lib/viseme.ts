export type Viseme = "rest" | "closed" | "narrow" | "mid" | "open" | "wide";

export const VISEME_MOUTH: Record<Viseme, { rx: number; ry: number; cy: number }> = {
  rest: { rx: 7, ry: 1.4, cy: 79 },
  closed: { rx: 6.5, ry: 1.1, cy: 80 },
  narrow: { rx: 7.5, ry: 2.2, cy: 80.5 },
  mid: { rx: 8.2, ry: 4.2, cy: 82 },
  open: { rx: 7.2, ry: 7.4, cy: 84 },
  wide: { rx: 11.2, ry: 3.1, cy: 81 },
};

const CLOSED = "mbp";
const NARROW = "fv";
const OPEN = "oouw";
const WIDE = "aei";

function visemeForChar(ch: string): Viseme {
  const c = ch.toLowerCase();
  if (!c.trim() || ".,!?;:'\"".includes(c)) return "closed";
  if (CLOSED.includes(c)) return "closed";
  if (NARROW.includes(c) || "sz".includes(c)) return "narrow";
  if (OPEN.includes(c)) return "open";
  if (WIDE.includes(c)) return "wide";
  return "mid";
}

export function visemeAt(text: string, time: number, speaking: boolean, duration = 0): Viseme {
  if (!speaking) return "rest";
  const words = (text || "").replace(/\s+/g, " ").trim().split(" ").filter(Boolean);
  if (!words.length) return "mid";
  const weights = words.map((word) => Math.max(word.replace(/[^a-z]/gi, "").length, 2) + 0.35);
  const totalWeight = weights.reduce((sum, weight) => sum + weight, 0);
  const span = duration > 0.4 ? duration : Math.max(totalWeight / 11, 0.8);
  let cursor = (Math.min(Math.max(0, time), span) / span) * totalWeight;
  for (let index = 0; index < words.length; index += 1) {
    const weight = weights[index];
    if (cursor <= weight) {
      const word = words[index];
      const letters = word.replace(/[^a-z]/gi, "") || word;
      const local = Math.min(0.999, cursor / weight);
      const idx = Math.floor(local * letters.length);
      const shape = visemeForChar(letters[idx] || "a");
      const gap = cursor / weight;
      if (gap > 0.92) return "closed";
      const wobble = Math.sin(time * 26);
      if (shape === "open" && wobble < -0.55) return "mid";
      if (shape === "wide" && wobble > 0.72) return "open";
      return shape;
    }
    cursor -= weight;
  }
  return "closed";
}

export function shouldBlink(time: number): boolean {
  const cycle = time % 3.4;
  return cycle > 3.22;
}
