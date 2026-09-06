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

const SPEECH_STOP = new Set(
  "a an the this that these those is are was were be been being to of in on at for from with as by or and if then else when while for do we you i it its it's into over about just also only more most such than so very can will would should could may might must here there now next first second last line code program method function class return true false null void public private static final new var let const".split(
    /\s+/,
  ),
);

function speechNeedles(speech: string): string[] {
  const text = speech || "";
  const quoted = [...text.matchAll(/`([^`]{2,80})`/g), ...text.matchAll(/"([^"]{2,48})"/g)]
    .map((match) => match[1].trim())
    .filter((item) => item.length > 1 && !/^(this|that|code|line|here)$/i.test(item));
  const lower = text.toLowerCase();
  const keywords: string[] = [];
  const maybe = (re: RegExp, ...tokens: string[]) => {
    if (re.test(lower)) keywords.push(...tokens);
  };
  maybe(/\bcallbacks?\b/, "callback");
  maybe(/\bpromises?\b/, "Promise", "new Promise");
  maybe(/\basync\b/, "async");
  maybe(/\bawait\b/, "await");
  maybe(/\.then\b|\bthen\s*\(/, ".then");
  maybe(/\.catch\b|\bcatch\s*\(/, ".catch", "catch");
  maybe(/\bresolve\b/, "resolve");
  maybe(/\breject\b/, "reject");
  maybe(/\bsettimeout\b/, "setTimeout");
  maybe(/\barraylist\b/, "ArrayList");
  maybe(/\bhashmap\b|\bmap\b/, "Map", "HashMap");
  maybe(/\bfor\s+loop\b|\bfor\s+each\b|\bforeach\b|\bfor\b/, "for");
  maybe(/\bwhile\b/, "while");
  maybe(/\bprintln\b|system\.out/, "println", "System.out");
  maybe(/\bprint\b/, "print");
  maybe(/\bconsole\.log\b/, "console.log");
  maybe(/\bappend\b/, "append");
  maybe(/\badd\(/, "add");
  maybe(/\blength\b/, "length");
  maybe(/\bsize\b/, "size");
  maybe(/\blist\b/, "list", "List");
  maybe(/\bdict\b/, "dict");
  maybe(/\btuple\b/, "tuple");
  maybe(/\bset\b/, "set");
  maybe(/\breturn\b/, "return");
  maybe(/\bif\b/, "if");
  maybe(/\belse\b/, "else");
  // Identifiers / type names spoken in the sentence (ArrayList, names, total, …)
  const ids = [...text.matchAll(/\b([A-Za-z_][\w.]{1,48})\b/g)]
    .map((match) => match[1])
    .filter((id) => id.length > 2 && !SPEECH_STOP.has(id.toLowerCase()));
  return [...quoted, ...keywords, ...ids];
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


export function teachingLineNumbers(code: string, ranges: HighlightRange[] = []): number[] {
  const lines = (code || "").replace(/\n$/, "").split("\n");
  const out: number[] = [];
  const pushRange = (from: number, to: number) => {
    for (let line = from; line <= to; line += 1) {
      if (!isBoilerplateLine(lines[line - 1] || "")) out.push(line);
    }
  };
  if (ranges.length) {
    for (const range of ranges) {
      const narrowed = narrowHighlight(code, range);
      if (!narrowed) continue;
      pushRange(narrowed.start_line, narrowed.end_line);
    }
  }
  if (!out.length) pushRange(1, lines.length);
  return [...new Set(out)];
}


export function highlightFromSpeechHints(
  code: string,
  ranges: HighlightRange[],
  speech: string,
  key?: string | null,
): HighlightRange | null {
  const lines = (code || "").replace(/\n$/, "").split("\n");
  const spoken = `${key || ""} ${speech || ""}`;

  const lineMention = spoken.match(/\bline\s+#?(\d+)\b/i);
  if (lineMention) {
    const line = Math.max(1, Math.min(lines.length, Number(lineMention[1])));
    if (line && !isBoilerplateLine(lines[line - 1] || "")) {
      return { start_line: line, end_line: line, start_col: 0, label: `line ${line}` };
    }
  }

  const keyText = (key || "").trim();
  if (keyText) {
    const byLabel = ranges.find(
      (range) => (range.label || "").trim().toLowerCase() === keyText.toLowerCase(),
    );
    if (byLabel) {
      const narrowed = narrowHighlight(code, byLabel);
      if (narrowed) {
        return { ...narrowed, end_line: narrowed.start_line };
      }
    }
  }
  return null;
}

export function progressiveHighlight(
  code: string,
  ranges: HighlightRange[],
  speech: string,
  cueIndex: number,
  cueCount = 0,
  key?: string | null,
): HighlightRange | null {
  const hinted = highlightFromSpeechHints(code, ranges, speech, key);
  if (hinted) return hinted;

  const teaching = teachingLineNumbers(code, ranges);
  if (!teaching.length) return highlightForSpeech(code, ranges, speech);

  // Spread highlights across teaching lines as narration advances.
  const total = Math.max(cueCount, cueIndex + 1, 1);
  const mapped =
    teaching.length === 1
      ? 0
      : Math.round((Math.min(cueIndex, total - 1) / Math.max(1, total - 1)) * (teaching.length - 1));
  const line = teaching[Math.max(0, Math.min(teaching.length - 1, mapped))];
  const matched = highlightForSpeech(code, ranges, speech);
  if (matched && teaching.includes(matched.start_line) && Math.abs(matched.start_line - line) <= 1) {
    return { ...matched, start_line: matched.start_line, end_line: matched.start_line };
  }
  return {
    start_line: line,
    end_line: line,
    start_col: 0,
    label: `line ${line}`,
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
