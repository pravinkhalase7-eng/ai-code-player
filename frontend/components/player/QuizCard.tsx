"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import type { LessonScene } from "@/types/lesson";
import { cn } from "@/lib/utils";

export function QuizCard({
  scene,
  onSubmit,
  result,
}: {
  scene: LessonScene;
  onSubmit: (answer: number | string, code?: string) => Promise<void>;
  result?: { status: string; explanation: string } | null;
}) {
  const [choice, setChoice] = useState<number | null>(null);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit() {
    setBusy(true);
    try {
      if (scene.kind === "fill_in_code" || scene.kind === "explain") {
        await onSubmit(text);
      } else if (scene.kind === "coding_challenge" || scene.kind === "modify_code") {
        await onSubmit(text, scene.starter_code || text);
      } else if (choice !== null) {
        await onSubmit(choice);
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="rounded-2xl border border-white/10 bg-zinc-950/40 p-5">
      <p className="mb-4 text-lg font-semibold text-white">{scene.question}</p>
      {scene.options?.length ? (
        <div className="grid gap-2">
          {scene.options.map((option, index) => (
            <button
              key={option}
              type="button"
              onClick={() => setChoice(index)}
              className={cn(
                "rounded-xl border px-4 py-3 text-left text-sm transition",
                choice === index
                  ? "border-amber-300 bg-amber-400/15 text-amber-50"
                  : "border-white/10 bg-white/5 text-zinc-200 hover:bg-white/10",
              )}
            >
              {option}
            </button>
          ))}
        </div>
      ) : (
        <textarea
          value={text}
          onChange={(event) => setText(event.target.value)}
          className="min-h-24 w-full rounded-xl border border-white/10 bg-zinc-950 p-3 font-mono text-sm"
          placeholder={scene.kind === "fill_in_code" ? "i++" : "Write your answer"}
        />
      )}
      <div className="mt-4 flex items-center justify-between gap-3">
        <Button onClick={submit} disabled={busy}>
          {busy ? "Checking..." : "Check answer"}
        </Button>
        {result ? (
          <p
            className={cn(
              "text-sm",
              result.status === "correct" ? "text-emerald-300" : "text-amber-200",
            )}
          >
            {result.explanation}
          </p>
        ) : null}
      </div>
    </div>
  );
}
