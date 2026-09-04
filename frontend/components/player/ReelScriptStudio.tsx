"use client";

import { Button } from "@/components/ui/button";
import { CodeWorkbench } from "@/components/editor/CodeWorkbench";
import { sourceFilename } from "@/lib/language";
import type { Lesson } from "@/types/lesson";

export type ScriptLine = {
  id: string;
  type: string;
  narration: string;
  takeaways?: string[];
};

export function ReelScriptStudio({
  lesson,
  code,
  lines,
  busy,
  error,
  onCodeChange,
  onNarrationChange,
  onRewrite,
  onConfirm,
  onClose,
}: {
  lesson: Lesson;
  code: string;
  lines: ScriptLine[];
  busy: string;
  error: string;
  onCodeChange: (value: string) => void;
  onNarrationChange: (id: string, narration: string) => void;
  onRewrite: () => void;
  onConfirm: () => void;
  onClose: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div className="flex max-h-[92vh] w-full max-w-5xl flex-col overflow-hidden rounded-3xl border border-white/10 bg-zinc-950 shadow-2xl">
        <div className="flex items-start justify-between gap-4 border-b border-white/10 px-5 py-4">
          <div>
            <p className="text-xs uppercase tracking-[0.22em] text-amber-300">Review before recording</p>
            <h2 className="mt-1 text-xl font-semibold text-white">Script and program</h2>
            <p className="mt-1 text-sm text-zinc-400">
              Edit what Byte says, or change the program and rewrite the script to match it. Nothing is recorded until you confirm.
            </p>
          </div>
          <Button size="sm" variant="ghost" onClick={onClose} disabled={Boolean(busy)}>
            Close
          </Button>
        </div>
        <div className="grid min-h-0 flex-1 gap-4 overflow-y-auto p-5 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
          <section>
            <p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-zinc-400">Program</p>
            <div className="h-[320px]">
              <CodeWorkbench
                code={code}
                language={lesson.language}
                filename={sourceFilename(lesson.language)}
                onChange={onCodeChange}
                compact
              />
            </div>
            <Button className="mt-3" size="sm" variant="outline" onClick={onRewrite} disabled={Boolean(busy)}>
              {busy === "rewrite" ? "Rewriting…" : "Rewrite script from this program"}
            </Button>
          </section>
          <section className="space-y-3">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-zinc-400">Spoken script</p>
            {lines.map((line) => (
              <label key={line.id} className="block">
                <span className="text-[11px] font-semibold uppercase tracking-[0.18em] text-amber-200/80">
                  {line.type}
                </span>
                <textarea
                  value={line.narration}
                  onChange={(event) => onNarrationChange(line.id, event.target.value)}
                  rows={line.type === "code" ? 5 : 3}
                  className="mt-1 w-full rounded-2xl border border-white/10 bg-white/5 px-3 py-2 text-sm leading-6 text-zinc-100 outline-none focus:border-amber-300/50"
                />
              </label>
            ))}
          </section>
        </div>
        {error ? <p className="px-5 pb-2 text-sm text-red-300">{error}</p> : null}
        <div className="flex flex-wrap justify-end gap-2 border-t border-white/10 px-5 py-4">
          <Button variant="outline" onClick={onClose} disabled={Boolean(busy)}>
            Cancel
          </Button>
          <Button onClick={onConfirm} disabled={Boolean(busy)}>
            {busy === "save" ? "Saving voice…" : busy === "record" ? "Recording video…" : "Use this script and record"}
          </Button>
        </div>
      </div>
    </div>
  );
}
