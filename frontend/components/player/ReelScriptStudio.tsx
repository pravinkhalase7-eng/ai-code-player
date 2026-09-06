"use client";

import { useMemo, useRef, useState } from "react";
import { Copy, Download, Film, ImageIcon, Play, Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { sourceFilename } from "@/lib/language";
import { buildThumbnailPrompt } from "@/lib/thumbnailPrompt";
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
  onUploadThumbnail,
  onCopyPrompt,
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
  onUploadThumbnail?: (file: File) => Promise<void> | void;
  onCopyPrompt?: (prompt: string) => Promise<void> | void;
}) {
  const locked = Boolean(busy);
  const fileRef = useRef<HTMLInputElement | null>(null);
  const [copyLabel, setCopyLabel] = useState("Copy");
  const [uploadBusy, setUploadBusy] = useState(false);
  const prompt = useMemo(() => buildThumbnailPrompt(lesson), [lesson]);
  const preview = lesson.thumbnail_url || "";

  async function handleCopy() {
    try {
      if (onCopyPrompt) {
        await onCopyPrompt(prompt);
      } else if (typeof navigator !== "undefined" && navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(prompt);
      }
      setCopyLabel("Copied");
      window.setTimeout(() => setCopyLabel("Copy"), 1600);
    } catch {
      setCopyLabel("Failed");
      window.setTimeout(() => setCopyLabel("Copy"), 1600);
    }
  }

  async function handleFile(file: File | undefined) {
    if (!file || !onUploadThumbnail) return;
    setUploadBusy(true);
    try {
      await onUploadThumbnail(file);
    } finally {
      setUploadBusy(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

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

          <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
            <div className="mb-3 flex items-center gap-2">
              <ImageIcon className="h-4 w-4 text-amber-300" />
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-zinc-300">Thumbnail</p>
              {lesson.thumbnail_custom ? (
                <span className="rounded-full bg-amber-400/15 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-amber-200">
                  Custom
                </span>
              ) : null}
            </div>
            {preview ? (
              <div className="mb-3 overflow-hidden rounded-xl border border-white/10 bg-black/40">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={preview} alt="Reel thumbnail preview" className="mx-auto max-h-56 w-auto object-contain" />
              </div>
            ) : (
              <p className="mb-3 rounded-xl border border-dashed border-white/10 px-3 py-6 text-center text-sm text-zinc-500">
                No thumbnail yet — generate externally or use auto SVG.
              </p>
            )}
            <label className="block">
              <span className="text-[11px] font-semibold uppercase tracking-[0.18em] text-zinc-500">
                Gemini image prompt
              </span>
              <textarea
                value={prompt}
                readOnly
                rows={8}
                className="mt-1 w-full resize-y rounded-2xl border border-white/10 bg-[#0b1220] px-3 py-2 font-mono text-[11px] leading-5 text-zinc-300 outline-none"
              />
            </label>
            <div className="mt-3 flex flex-wrap gap-2">
              <Button type="button" size="sm" variant="outline" onClick={() => void handleCopy()} disabled={locked}>
                <Copy className="h-4 w-4" />
                {copyLabel}
              </Button>
              <Button
                type="button"
                size="sm"
                variant="outline"
                onClick={() => fileRef.current?.click()}
                disabled={locked || uploadBusy || !onUploadThumbnail}
              >
                <Upload className="h-4 w-4" />
                {uploadBusy ? "Uploading…" : "Upload"}
              </Button>
              <input
                ref={fileRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={(event) => void handleFile(event.target.files?.[0])}
              />
            </div>
            <p className="mt-2 text-xs text-zinc-500">
              Upload replaces auto thumbnail; regenerate uses fallback.
            </p>
          </div>
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
