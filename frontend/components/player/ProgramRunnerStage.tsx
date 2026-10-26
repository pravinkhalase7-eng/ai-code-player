"use client";

import { useMemo } from "react";
import { TalkingByteAvatar } from "@/components/tutor/TalkingByteAvatar";
import { KaraokeCaption } from "@/components/player/Caption";
import { ReelCodePanel } from "@/components/player/ReelCodePanel";
import { buildCues, cueAt } from "@/lib/narrationSync";
import { beatHighlight, debugBeats, reelBeatAt } from "@/lib/reelDebugSync";
import { formatResultChip, typedCode, typingCaretHighlight } from "@/lib/programRunner";
import { sourceFilename } from "@/lib/language";
import { displayTopic, stripDurationNoise } from "@/lib/reelHeadlines";
import { cn } from "@/lib/utils";
import type { ExecutionStep, HighlightRange, Lesson, LessonScene } from "@/types/lesson";

export function ProgramRunnerStage({
  lesson,
  scene,
  code,
  caption,
  highlight,
  playing,
  currentTime,
  duration,
  terminalLines = [],
  runError,
  iterations = [],
  sceneIndex = 0,
  sceneCount = 2,
  splitScreen = false,
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
  sceneIndex?: number;
  sceneCount?: number;
  splitScreen?: boolean;
}) {
  const typing = scene.type === "code";
  const running = scene.type === "execution" || scene.type === "terminal";
  const timedScene = useMemo(
    () => (iterations.length ? { ...scene, iterations } : scene),
    [scene, iterations],
  );
  const beats = useMemo(
    () => (running ? debugBeats(timedScene, code, duration) : []),
    [running, timedScene, code, duration],
  );
  const narrationCues = useMemo(() => buildCues(scene, duration), [scene, duration]);
  const beat = running ? reelBeatAt(beats, currentTime) : null;
  const spokenCue = cueAt(narrationCues, currentTime);
  const revealed = typing ? typedCode(code, currentTime, duration, narrationCues) : code;
  const activeHighlight = running
    ? beatHighlight(beat)
    : typing
      ? typingCaretHighlight(revealed)
      : spokenCue?.highlight || highlight;
  const printed = (beat?.output?.length ? beat.output : terminalLines) ?? [];
  const latest = beat?.latest ?? (printed.length ? printed[printed.length - 1] : undefined);
  const narration = stripDurationNoise(scene.narration || caption);
  const spokenCaption = stripDurationNoise(caption);
  const karaokeText = stripDurationNoise(spokenCue?.text || spokenCaption || scene.narration || "");
  const karaokeStart = spokenCue?.start ?? 0;
  const karaokeEnd = spokenCue?.end ?? Math.max(duration, karaokeStart + 0.5);
  const topic = displayTopic(lesson.topic);
  const progress = duration > 0 ? Math.min(1, Math.max(0, currentTime / duration)) : 0;
  const filename = scene.filename || sourceFilename(lesson.language);

  return (
    <div className="reel-stage relative flex h-full max-h-full w-auto max-w-full aspect-[9/16] flex-col overflow-hidden rounded-[2rem] border border-white/12 bg-[#1e1e1e] px-3 pb-3 pt-3 shadow-[0_30px_80px_rgba(0,0,0,0.55)]">
      <div className="relative z-20 flex gap-1">
        {Array.from({ length: Math.max(1, sceneCount) }).map((_, index) => (
          <div key={index} className="h-[3px] flex-1 overflow-hidden rounded-full bg-white/25">
            <div
              className="h-full rounded-full bg-white"
              style={{
                width:
                  index < sceneIndex ? "100%" : index === sceneIndex ? `${Math.round(progress * 100)}%` : "0%",
              }}
            />
          </div>
        ))}
      </div>

      <div
        className={cn(
          "mt-2 flex min-h-0 flex-col",
          splitScreen ? "h-1/2 shrink-0" : "flex-1",
        )}
      >
      <header className={cn("relative z-10 px-1", splitScreen ? "mb-1" : "mb-2")}>
        <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-zinc-400">
          {typing ? "Watch it type" : "Watch it run"} · {lesson.language}
        </p>
        <h2
          className={cn(
            "mt-1 font-extrabold tracking-tight text-white",
            splitScreen ? "text-[1.15rem] leading-6" : "text-[1.65rem] leading-8",
          )}
        >
          {topic}
        </h2>
      </header>

      <div className="relative z-10 flex min-h-0 flex-1 flex-col overflow-hidden rounded-2xl border border-white/10 bg-[#1e1e1e]">
        <ReelCodePanel
          code={revealed || " "}
          filename={filename}
          highlight={activeHighlight}
          caret={typing && revealed.length < (code || "").length}
          syntax
          vivid
        />
        {running ? (
          <div className="shrink-0 border-t border-white/10 bg-black/70 px-3 py-2">
            <p className="mb-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-zinc-500">Terminal</p>
            <div className={cn("overflow-y-auto font-mono text-[16px] font-semibold leading-6 text-zinc-100", splitScreen ? "max-h-24" : "max-h-32")}>
              {printed.length === 0 && !runError && !scene.stderr ? (
                <p className="text-zinc-500">$ python {filename}</p>
              ) : (
                printed.slice(-6).map((line, index) => (
                  <p
                    key={`${index}-${line}`}
                    className={cn(
                      "truncate",
                      Boolean(latest) && line === latest && "font-semibold text-white",
                    )}
                  >
                    {formatResultChip(line)}
                  </p>
                ))
              )}
              {runError || scene.stderr ? (
                <p className="max-h-16 overflow-y-auto whitespace-pre-wrap text-red-300">
                  {runError || scene.stderr}
                </p>
              ) : null}
            </div>
          </div>
        ) : null}
      </div>
      </div>

      <div
        className={cn(
          "relative z-20 mt-2 flex min-h-0",
          splitScreen ? "flex-1 flex-col items-center justify-end gap-3 pb-1" : "shrink-0 items-end gap-2",
        )}
      >
        {running && beat ? (
          <p className="w-full shrink-0 rounded-xl border border-amber-300/20 bg-amber-400/10 px-3 py-1.5 text-left text-[13px] font-semibold text-amber-100">
            {beat.label}
            {beat.description ? ` · ${beat.description}` : ""}
          </p>
        ) : null}
        <TalkingByteAvatar
          speaking={playing}
          narration={narration}
          currentTime={currentTime}
          duration={duration}
          size={splitScreen && !running ? "lg" : "sm"}
        />
        <KaraokeCaption
          text={karaokeText}
          currentTime={currentTime}
          duration={duration}
          cueStart={karaokeStart}
          cueEnd={karaokeEnd}
          segments={scene.segments}
          className={splitScreen ? "w-full text-base" : undefined}
        />
      </div>
    </div>
  );
}
