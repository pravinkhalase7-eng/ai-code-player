import type { HighlightRange } from "@/types/lesson";

export function isBoilerplateLine(line: string): boolean {
  const text = line.trim();
  if (!text) return true;
  if (/^[{}();,\[\]]+$/.test(text)) return true;
  if (/^(import|from|package|using)\b/.test(text)) return true;
  if (/^(public\s+)?(class|interface)\s+\w+/.test(text)) return true;
  if (/public\s+static\s+void\s+main\s*\(/.test(text)) return true;
  if (/^(export\s+)?(default\s+)?function\s+main\b/.test(text)) return true;
  if (/^def\s+main\b/.test(text)) return true;
  return false;
}

export function narrowHighlight(code: string, range: HighlightRange | null): HighlightRange | null {
  if (!range) return null;
  const lines = (code || "").replace(/\n$/, "").split("\n");
  if (!lines.length) return null;
  const start = Math.max(0, range.start_line - 1);
  const end = Math.min(lines.length - 1, Math.max(start, (range.end_line || range.start_line) - 1));
  let from = start;
  let to = end;
  while (from <= to && isBoilerplateLine(lines[from])) from += 1;
  while (to >= from && isBoilerplateLine(lines[to])) to -= 1;
  if (from > to) return null;
  return { ...range, start_line: from + 1, end_line: to + 1 };
}

function speechNeedles(speech: string): string[] {
  const text = speech || "";
  const quoted = [...text.matchAll(/`([^`]{2,80})`/g), ...text.matchAll(/"([^"]{2,48})"/g)]
    .map((match) => match[1].trim())
    .filter((item) => item.length > 1 && !/^(this|that|code|line|here)$/i.test(item));
  const lower = text.toLowerCase();
  const keywords: string[] = [];
  if (/\bcallbacks?\b/.test(lower)) keywords.push("callback");
  if (/\bpromises?\b/.test(lower)) keywords.push("Promise", "new Promise");
  if (/\basync\b/.test(lower)) keywords.push("async");
  if (/\bawait\b/.test(lower)) keywords.push("await");
  if (/\.then\b|\bthen\s*\(/.test(lower)) keywords.push(".then");
  if (/\.catch\b|\bcatch\s*\(/.test(lower)) keywords.push(".catch", "catch");
  if (/\bresolve\b/.test(lower)) keywords.push("resolve");
  if (/\breject\b/.test(lower)) keywords.push("reject");
  if (/\bsettimeout\b/.test(lower)) keywords.push("setTimeout");
  return [...quoted, ...keywords];
}

function lineScore(line: string, needles: string[]): number {
  if (isBoilerplateLine(line)) return 0;
  const hay = line.toLowerCase();
  let score = 0;
  for (const needle of needles) {
    const token = needle.toLowerCase();
    if (token.length < 2) continue;
    if (hay.includes(token)) score += Math.min(token.length, 14);
  }
  return score;
}

function bestLineInRange(
  lines: string[],
  startLine: number,
  endLine: number,
  needles: string[],
): number {
  let best = startLine;
  let bestScore = 0;
  for (let line = startLine; line <= endLine; line += 1) {
    const score = lineScore(lines[line - 1] || "", needles);
    if (score > bestScore) {
      bestScore = score;
      best = line;
    }
  }
  return bestScore > 0 ? best : -1;
}

export function highlightForSpeech(
  code: string,
  ranges: HighlightRange[],
  speech: string,
): HighlightRange | null {
  const lines = (code || "").replace(/\n$/, "").split("\n");
  const needles = speechNeedles(speech);
  if (!needles.length || !lines.length) return null;

  let bestRange: HighlightRange | null = null;
  let bestScore = 0;
  for (const range of ranges) {
    const narrowed = narrowHighlight(code, range);
    if (!narrowed) continue;
    const snippet = lines.slice(narrowed.start_line - 1, narrowed.end_line).join("\n");
    const score = lineScore(snippet, needles);
    if (score > bestScore) {
      bestScore = score;
      bestRange = narrowed;
    }
  }
  if (bestRange && bestScore > 0) {
    const focused = bestLineInRange(lines, bestRange.start_line, bestRange.end_line, needles);
    if (focused > 0) {
      return { ...bestRange, start_line: focused, end_line: focused };
    }
    return bestRange;
  }

  const focused = bestLineInRange(lines, 1, lines.length, needles);
  if (focused < 0) return null;
  return {
    start_line: focused,
    end_line: focused,
    start_col: 0,
    label: needles[0],
  };
}

export function firstMeaningfulHighlight(code: string, ranges: HighlightRange[]): HighlightRange | null {
  for (const range of ranges) {
    const narrowed = narrowHighlight(code, range);
    if (narrowed) {
      const lines = (code || "").split("\n");
      const teaching = bestLineInRange(
        lines,
        narrowed.start_line,
        narrowed.end_line,
        ["callback", "Promise", "async", "await", ".then", "resolve"],
      );
      if (teaching > 0) {
        return { ...narrowed, start_line: teaching, end_line: teaching };
      }
      return { ...narrowed, end_line: narrowed.start_line };
    }
  }
  return null;
}
