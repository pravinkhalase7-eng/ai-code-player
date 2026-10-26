import { wordsForSpan } from "@/lib/karaokeCaption";
import type { ExecutionStep, HighlightRange, LessonScene } from "@/types/lesson";

export type ReelBeat = {
  start: number;
  end: number;
  line: number;
  label: string;
  description: string;
  output: string[];
  latest?: string;
  variables: { name: string; value: string }[];
  condition?: string | null;
  condition_result?: boolean | null;
  stopped?: boolean;
};

export function printStatementLine(code: string): number {
  const lines = (code || "").split("\n");
  const index = lines.findIndex((line) =>
    /System\.out\s*\.|console\.log\s*\(|\bprint(ln)?\s*\(/i.test(line),
  );
  return index >= 0 ? index + 1 : 1;
}

function printSteps(scene: LessonScene, code: string): ExecutionStep[] {
  const fromIterations = (scene.iterations || []).filter((step) => Boolean(step.output_line));
  if (fromIterations.length) return fromIterations;
  const stdout = scene.stdout?.length ? scene.stdout : scene.expected_output || [];
  const line = printStatementLine(code);
  return stdout.map((text, index) => ({
    index: index + 1,
    label: `print ${index + 1}`,
    description: `prints ${text}`,
    line,
    output_line: String(text),
    variables: [],
  }));
}

function lineForOutput(code: string, output: string | undefined, fallback: number): number {
  const lines = (code || "").replace(/\n$/, "").split("\n");
  const needle = String(output || "").replace(/^"|"$/g, "").trim();
  if (needle) {
    for (let index = 0; index < lines.length; index += 1) {
      if (lines[index].includes(needle)) return index + 1;
    }
  }
  for (let index = 0; index < lines.length; index += 1) {
    if (/\b(println|print|console\.log)\s*\(/.test(lines[index])) return index + 1;
  }
  return fallback;
}

export function reelBeats(scene: LessonScene, code: string, duration: number): ReelBeat[] {
  const steps = printSteps(scene, code);
  if (!steps.length) return [];
  const highlightLine = printStatementLine(code) || steps[0].line || 1;
  const span = Math.max(duration, 0.4);
  const slice = span / steps.length;
  return steps.map((step, index) => {
    const output = steps.slice(0, index + 1).map((item) => String(item.output_line));
    const latest = String(step.output_line);
    return {
      start: index * slice,
      end: index === steps.length - 1 ? span + 0.05 : (index + 1) * slice,
      line: lineForOutput(code, latest, step.line || highlightLine),
      label: "print",
      description: latest,
      output,
      latest,
      variables: (step.variables || []).map((item) => ({ name: item.name, value: item.value })),
      condition: step.condition,
      condition_result: step.condition_result,
      stopped: step.stopped,
    };
  });
}

function sourceLine(code: string, line: number | undefined): string {
  const lines = (code || "").replace(/\n$/, "").split("\n");
  return lines[Math.max(0, (line || 1) - 1)] || "";
}

function isRuntimeStep(step: ExecutionStep, code: string): boolean {
  if (step.output_line) return true;
  const raw = sourceLine(code, step.line);
  const text = raw.trim();
  if (!text || text.startsWith("#")) return false;
  if (/^(class |def )/i.test(text)) return false;
  if (/^\s+/.test(raw)) return false;
  if (/=/.test(text) && /\(/.test(text) && !/\bprint(ln)?\s*\(/.test(text)) return false;
  return true;
}

const STEP_STOP = new Set(["print", "println", "self", "def", "class", "this", "return", "true", "false", "none", "null"]);

function stepNeedles(step: ExecutionStep, code: string): string[] {
  const line = sourceLine(code, step.line);
  const blob = `${step.description || ""} ${step.output_line || ""} ${line}`;
  const quoted = [...blob.matchAll(/["']([^"']{2,48})["']/g)].map((match) => match[1]);
  const ids = [...blob.matchAll(/[A-Za-z_][A-Za-z0-9_.]{2,}/g)].map((match) => match[0]);
  const out = String(step.output_line || "")
    .split(/[\s:]+/)
    .filter((word) => word.length > 2);
  return [...quoted, ...ids, ...out].filter((token) => {
    const key = token.toLowerCase().replace(/[^a-z0-9_]/g, "");
    return key.length > 2 && !STEP_STOP.has(key);
  });
}

function tokenMatches(word: string, needle: string): boolean {
  const a = word.toLowerCase().replace(/^[^a-z0-9_]+|[^a-z0-9_]+$/g, "");
  const b = needle.toLowerCase().replace(/^[^a-z0-9_]+|[^a-z0-9_]+$/g, "");
  if (!a || !b) return false;
  if (a === b) return true;
  if (a.length > 3 && b.includes(a)) return true;
  if (b.length > 3 && a.includes(b)) return true;
  return false;
}

function alignStepsToSpeech(steps: ExecutionStep[], narration: string, code: string, duration: number): number[] {
  const span = Math.max(duration, 0.4);
  const words = wordsForSpan(narration || "", 0, span);
  const starts = steps.map(() => -1);
  let wordIndex = 0;
  steps.forEach((step, index) => {
    const needles = stepNeedles(step, code);
    if (!needles.length || !words.length) return;
    for (let cursor = wordIndex; cursor < words.length; cursor += 1) {
      if (needles.some((needle) => tokenMatches(words[cursor].text, needle))) {
        starts[index] = words[cursor].start;
        wordIndex = cursor + 1;
        return;
      }
    }
  });
  let last = 0;
  for (let index = 0; index < starts.length; index += 1) {
    if (starts[index] >= 0) {
      last = starts[index];
      continue;
    }
    let next = span;
    for (let look = index + 1; look < starts.length; look += 1) {
      if (starts[look] >= 0) {
        next = starts[look];
        break;
      }
    }
    let run = 1;
    while (index + run < starts.length && starts[index + run] < 0) run += 1;
    const gap = Math.max(0.16, next - last);
    for (let offset = 0; offset < run; offset += 1) {
      starts[index + offset] = last + (gap * (offset + 1)) / (run + 1);
    }
    index += run - 1;
  }
  for (let index = 1; index < starts.length; index += 1) {
    if (starts[index] < starts[index - 1]) starts[index] = starts[index - 1] + 0.04;
  }
  return starts.map((value) => Math.max(0, value));
}

function withMissingPrints(scene: LessonScene, steps: ExecutionStep[], code: string): ExecutionStep[] {
  const seen = new Set(
    steps.map((step) => String(step.output_line || "").trim()).filter(Boolean),
  );
  const extra = (scene.expected_output || scene.stdout || []).filter(
    (line) => !seen.has(String(line).trim()),
  );
  if (!extra.length) return steps;
  const fallback = printStatementLine(code);
  return [
    ...steps,
    ...extra.map((text, index) => ({
      index: steps.length + index + 1,
      label: `print ${seen.size + index + 1}`,
      description: String(text),
      line: lineForOutput(code, String(text), fallback),
      output_line: String(text),
      variables: [],
    })),
  ];
}

export function debugBeats(scene: LessonScene, code: string, duration: number): ReelBeat[] {
  const raw = (scene.iterations || []).length ? scene.iterations! : printSteps(scene, code);
  const filled = withMissingPrints(scene, raw, code);
  const runtime = filled.filter((step) => isRuntimeStep(step, code));
  const steps = runtime.length ? runtime : filled;
  if (!steps.length) return reelBeats(scene, code, duration);
  const span = Math.max(duration, 0.4);
  const starts = alignStepsToSpeech(steps, scene.narration || "", code, span);
  const printed: string[] = [];
  return steps.map((step, index) => {
    if (step.output_line) printed.push(String(step.output_line));
    const start = starts[index] ?? (index / steps.length) * span;
    const end = index === steps.length - 1 ? span + 0.05 : Math.max(start + 0.08, starts[index + 1] ?? span);
    const latest = printed.length ? printed[printed.length - 1] : undefined;
    return {
      start,
      end,
      line: step.line || printStatementLine(code) || 1,
      label: step.label || `step ${index + 1}`,
      description: step.description || String(step.output_line || ""),
      output: [...printed],
      latest,
      variables: (step.variables || []).map((item) => ({ name: item.name, value: item.value })),
      condition: step.condition,
      condition_result: step.condition_result,
      stopped: step.stopped,
    };
  });
}

export function reelBeatAt(beats: ReelBeat[], time: number): ReelBeat | null {
  if (!beats.length) return null;
  const t = Math.max(0, time);
  return beats.find((beat) => t >= beat.start && t < beat.end) || beats[beats.length - 1];
}

export function beatHighlight(beat: ReelBeat | null): HighlightRange | null {
  if (!beat) return null;
  return {
    start_line: beat.line,
    end_line: beat.line,
    start_col: 0,
    label: beat.label || "step",
  };
}
