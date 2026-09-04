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
      line: highlightLine,
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
    label: "print",
  };
}
