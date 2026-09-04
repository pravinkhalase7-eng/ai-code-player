"use client";

import { useMemo } from "react";
import { TalkingByteAvatar } from "@/components/tutor/TalkingByteAvatar";
import { ReelCodePanel } from "@/components/player/ReelCodePanel";
import { sourceFilename } from "@/lib/language";
import { beatHighlight, reelBeatAt, reelBeats } from "@/lib/reelDebugSync";
import { cn } from "@/lib/utils";
import type { ExecutionStep, HighlightRange, Lesson, LessonScene } from "@/types/lesson";

export function ReelStage({
  lesson,
  scene,
  code,
  caption,
  highlight,
  playing,
  currentTime,
  duration,
  runError,
  iterations = [],
}: {
  lesson: Lesson;
  scene: LessonScene;
  code: string;
  caption: string;
  highlight: HighlightRange | null;
  playing: boolean;
  currentTime: number;
  duration: number;
  terminalLines: string[];
  runError: string;
  iterations?: ExecutionStep[];
  stepIndex?: number;
  onChangeCode?: (value: string) => void;
}) {
  const running = scene.type === "execution" || scene.type === "terminal";
  const timedScene = useMemo(
    () => (iterations.length ? { ...scene, iterations } : scene),
    [scene, iterations],
  );
  const beats = useMemo(
    () => (running ? reelBeats(timedScene, code, duration) : []),
    [running, timedScene, code, duration],
  );
  const beat = running ? reelBeatAt(beats, currentTime) : null;
  const activeHighlight = running ? beatHighlight(beat) : highlight;
  const printed = beat?.output ?? [];
  const latest = beat?.latest;
  const narration = scene.narration || caption;
  const showConsole = running || Boolean(runError || scene.stderr);

  return (
    <div className="reel-stage relative flex h-full max-h-full w-auto max-w-full aspect-[9/16] flex-col overflow-hidden rounded-[2rem] border border-white/12 px-3 pb-3 pt-3 shadow-[0_30px_80px_rgba(0,0,0,0.55)]">
      <div className="reel-stage-vignette pointer-events-none absolute inset-0 z-[1]" />

      <header className="relative z-10 shrink-0 text-center">
        <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-cyan-100/80">
          {lesson.language}
        </p>
        <p className="truncate text-sm font-semibold leading-5 text-white">{lesson.topic}</p>
      </header>

      <div className="relative z-10 flex min-h-0 flex-1 flex-col items-stretch justify-center py-2">
        <div className="flex max-h-full min-h-0 flex-col overflow-hidden rounded-2xl border border-cyan-200/20 bg-[#07111f]/92 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]">
          <ReelCodePanel
            code={code}
            filename={scene.filename || sourceFilename(lesson.language)}
            highlight={activeHighlight}
          />
          {showConsole ? (
            <div className="shrink-0 border-t border-amber-300/25 bg-black/55 px-3 py-2">
              <div className="mb-1 flex items-center justify-between gap-2">
                <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-amber-300">
                  {beat ? `Output · ${beat.label}` : "Output"}
                </p>
                {beat?.variables?.length ? (
                  <div className="flex flex-wrap justify-end gap-1">
                    {beat.variables.map((item) => (
                      <span
                        key={`${item.name}-${item.value}`}
                        className="rounded bg-zinc-950 px-1.5 py-0.5 font-mono text-[10px] text-amber-200"
                      >
                        {item.name}={item.value}
                      </span>
                    ))}
                  </div>
                ) : null}
              </div>
              {beat?.condition ? (
                <p className="mb-1 font-mono text-[10px] text-zinc-400">
                  {beat.condition} → {beat.condition_result ? "true" : "false"}
                  {beat.stopped ? " · stop" : ""}
                </p>
              ) : null}
              <div className="max-h-24 overflow-hidden font-mono text-[11px] leading-4 text-zinc-200">
                {printed.length === 0 && !runError && !scene.stderr ? (
                  <p className="text-zinc-500">waiting for print…</p>
                ) : (
                  printed.map((line, index) => (
                    <p
                      key={`${index}-${line}`}
                      className={cn("truncate", Boolean(latest) && line === latest && "text-amber-100")}
                    >
                      <span className="text-zinc-500">&gt; </span>
                      {line}
                    </p>
                  ))
                )}
                {runError || scene.stderr ? (
                  <p className="truncate text-red-300">{runError || scene.stderr}</p>
                ) : null}
              </div>
            </div>
          ) : null}
        </div>
      </div>

      <div className="relative z-10 flex shrink-0 items-end gap-3">
        <TalkingByteAvatar
          speaking={playing}
          narration={narration}
          currentTime={currentTime}
          duration={duration}
          size="lg"
        />
        <div className="mb-1 min-w-0 flex-1 rounded-2xl border border-white/10 bg-black/60 px-3 py-2.5 backdrop-blur-md">
          <p className={cn("text-sm font-medium leading-5 text-white", "line-clamp-3")}>
            {running && beat?.description ? beat.description : caption}
          </p>
          {activeHighlight?.label ? (
            <p className="mt-1 text-[10px] uppercase tracking-[0.22em] text-amber-300">{activeHighlight.label}</p>
          ) : null}
        </div>
      </div>
    </div>
  );
}
