"use client";

import { ChevronLeft, ChevronRight, Pause, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { VariablePanel } from "@/components/player/VariablePanel";
import type { ExecutionStep } from "@/types/lesson";

export function ExecutionStepper({
  steps,
  stepIndex,
  onStep,
  onRestart,
  manual,
}: {
  steps: ExecutionStep[];
  stepIndex: number;
  onStep: (next: number) => void;
  onRestart: () => void;
  manual: boolean;
}) {
  if (!steps.length) return null;
  const bounded = Math.min(Math.max(0, stepIndex), steps.length - 1);
  const current = steps[bounded];
  return (
    <div className="mt-4 space-y-3 rounded-2xl border border-amber-300/20 bg-amber-400/5 p-4">
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-amber-200">
          Step {bounded + 1} of {steps.length}
          {manual ? "" : " · following voice"}
        </p>
        <div className="flex gap-1">
          <Button type="button" size="sm" variant="ghost" onClick={() => onStep(bounded - 1)} disabled={bounded <= 0}>
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <Button
            type="button"
            size="sm"
            variant="ghost"
            onClick={() => onStep(Math.min(steps.length - 1, bounded + 1))}
            disabled={bounded >= steps.length - 1}
          >
            <ChevronRight className="h-4 w-4" /> Step
          </Button>
          <Button type="button" size="sm" variant="ghost" onClick={onRestart}>
            <RotateCcw className="h-4 w-4" />
          </Button>
        </div>
      </div>
      <p className="font-mono text-sm text-amber-100">{current.label}: {current.description}</p>
      {current.condition ? (
        <p className="text-xs text-zinc-400">
          {current.condition} → {current.condition_result ? "true" : "false"}
          {current.stopped ? " · loop stops" : ""}
        </p>
      ) : null}
      {!manual ? (
        <p className="flex items-center gap-1 text-xs text-zinc-500">
          <Pause className="h-3 w-3" /> Click Step to freeze the walkthrough
        </p>
      ) : null}
      <VariablePanel variables={current.variables ?? []} />
    </div>
  );
}
