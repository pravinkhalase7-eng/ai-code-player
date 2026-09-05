"use client";

import { Download, Film, Play } from "lucide-react";
import { Button } from "@/components/ui/button";
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
  onPlay,
  onRecord,
  onDownload,
  downloading,
  explainOnly = false,
}: {
  lesson: Lesson;
  code: string;
  lines: ScriptLine[];
  busy: string;
  error: string;
  onCodeChange: (value: string) => void;
  onNarrationChange: (id: string, narration: string) => void;
  onRewrite: () => void;
  onPlay: () => void;
  onRecord: () => void;
  onDownload: () => void;
  downloading?: boolean;
  explainOnly?: boolean;
}) {
  const locked = Boolean(busy);
  return (
    <div className="flex min-h-[72vh] flex-1 flex-col overflow-hidden rounded-3xl border border-white/10 bg-zinc-950">
      <div className="border-b border-white/10 px-5 py-4">
        <p className="text-xs uppercase tracking-[0.22em] text-amber-300">Review before playing</p>
        <h2 className="mt-1 text-xl font-semibold text-white">{explainOnly ? "Explain script" : "Script and program"}</h2>
        <p className="mt-1 text-sm text-zinc-400">
          {explainOnly
            ? "Edit the spoken lines for this info reel. There is no program — playback stays off until you choose a button below."
            : "Edit the spoken lines and the program here first. Playback and recording stay off until you choose one of the buttons below."}
        </p>
      </div>
      <div className={`grid min-h-0 flex-1 gap-4 overflow-y-auto p-5 ${explainOnly ? "" : "lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]"}`}>
        {explainOnly ? null : (
        <section className="flex min-h-0 flex-col">
          <p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-zinc-400">
            Program · {sourceFilename(lesson.language)}
          </p>
          <textarea
            value={code}
            onChange={(event) => onCodeChange(event.target.value)}
            spellCheck={false}
            disabled={locked}
            className="min-h-[280px] flex-1 resize-y rounded-2xl border border-white/10 bg-[#0b1220] px-4 py-3 font-mono text-[13px] leading-6 text-zinc-100 outline-none focus:border-amber-300/50"
          />
          <Button className="mt-3 self-start" type="button" size="sm" variant="outline" onClick={onRewrite} disabled={locked}>
            {busy === "rewrite" ? "Rewriting…" : "Rewrite script from this program"}
          </Button>
        </section>
        )}
        <section className="space-y-3">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-zinc-400">Spoken script</p>
          {lines.length ? (
            lines.map((line) => (
              <label key={line.id} className="block">
                <span className="text-[11px] font-semibold uppercase tracking-[0.18em] text-amber-200/80">
                  {line.type}
                </span>
                <textarea
                  value={line.narration}
                  onChange={(event) => onNarrationChange(line.id, event.target.value)}
                  rows={line.type === "code" ? 6 : 4}
                  disabled={locked}
                  className="mt-1 w-full rounded-2xl border border-white/10 bg-white/5 px-3 py-2 text-sm leading-6 text-zinc-100 outline-none focus:border-amber-300/50"
                />
              </label>
            ))
          ) : (
            <p className="rounded-2xl border border-white/10 bg-white/5 px-3 py-4 text-sm text-zinc-400">
              No spoken lines yet. Wait for the short to finish generating, then refresh.
            </p>
          )}
        </section>
      </div>
      {error ? <p className="px-5 pb-2 text-sm text-red-300">{error}</p> : null}
      <div className="flex flex-wrap justify-end gap-2 border-t border-white/10 px-5 py-4">
        <Button type="button" variant="outline" onClick={onDownload} disabled={locked || downloading}>
          <Download className="h-4 w-4" />
          {busy === "record" || downloading ? "Exporting…" : "Download video"}
        </Button>
        <Button type="button" variant="outline" onClick={onRecord} disabled={locked}>
          <Film className="h-4 w-4" />
          {busy === "save" ? "Saving voice…" : busy === "record" ? "Recording video…" : "Record video"}
        </Button>
        <Button type="button" onClick={onPlay} disabled={locked}>
          <Play className="h-4 w-4" />
          {busy === "save" ? "Saving voice…" : "Play this short"}
        </Button>
      </div>
    </div>
  );
}
