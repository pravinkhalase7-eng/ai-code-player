"use client";

import { useMemo } from "react";
import { TalkingByteAvatar } from "@/components/tutor/TalkingByteAvatar";
import { KaraokeCaption } from "@/components/player/Caption";
import { ReelCodePanel } from "@/components/player/ReelCodePanel";
import { buildCues, cueAt } from "@/lib/narrationSync";
import { beatHighlight, debugBeats, reelBeatAt } from "@/lib/reelDebugSync";
import { isProgramRunnerLesson, typedCode, typingCaretHighlight } from "@/lib/programRunner";
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
}) {
  const runnerLesson = isProgramRunnerLesson(lesson);
  const typing = runnerLesson && scene.type === "code";
  const running = scene.type === "execution" || scene.type === "terminal";
  const timedScene = useMemo(
    () => (iterations.length ? { ...scene, iterations } : scene),
    [scene, iterations],
  );
  const beats = useMemo(
    () => (running ? debugBeats(timedScene, code, duration) : []),
    [running, timedScene, code, duration],
  );
  const beat = running ? reelBeatAt(beats, currentTime) : null;
  const revealed = typing ? typedCode(code, currentTime, duration) : code;
  const activeHighlight = typing
    ? typingCaretHighlight(revealed)
    : running
      ? beatHighlight(beat)
      : highlight;
  const printed = (beat?.output?.length ? beat.output : terminalLines) ?? [];
  const latest = beat?.latest ?? (printed.length ? printed[printed.length - 1] : undefined);
  const narration = stripDurationNoise(scene.narration || caption);
  const spokenCaption = stripDurationNoise(caption);
  const narrationCues = useMemo(() => buildCues(scene, duration), [scene, duration]);
  const karaokeCue = cueAt(narrationCues, currentTime);
  const karaokeText = stripDurationNoise(karaokeCue?.text || spokenCaption || scene.narration || "");
  const karaokeStart = karaokeCue?.start ?? 0;
  const karaokeEnd = karaokeCue?.end ?? Math.max(duration, karaokeStart + 0.5);
  const topic = displayTopic(lesson.topic);
  const progress = duration > 0 ? Math.min(1, Math.max(0, currentTime / duration)) : 0;
  const explainBody = running && beat?.description ? beat.description : karaokeText;
  const filename = scene.filename || sourceFilename(lesson.language);

  return (
    <div className="relative flex h-full max-h-full w-full max-w-5xl flex-col overflow-hidden rounded-[1.6rem] border border-white/12 bg-[#070b12] px-3 pb-3 pt-3 shadow-[0_30px_80px_rgba(0,0,0,0.55)] aspect-[16/10] max-md:aspect-[4/5]">
      <div className="relative z-20 flex gap-1">
        {Array.from({ length: Math.max(1, sceneCount) }).map((_, index) => (
          <div key={index} className="h-[3px] flex-1 overflow-hidden rounded-full bg-white/25">
            <div
              className="h-full rounded-full bg-lime-300"
              style={{
                width:
                  index < sceneIndex ? "100%" : index === sceneIndex ? `${Math.round(progress * 100)}%` : "0%",
              }}
            />
          </div>
        ))}
      </div>

      <header className="mt-2 flex flex-wrap items-center gap-2">
        <p className="rounded-full border border-cyan-200/30 bg-cyan-300/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-cyan-100">
          {lesson.language}
        </p>
        <p className="rounded-full border border-lime-300/40 bg-lime-400/15 px-2.5 py-0.5 text-[10px] font-extrabold uppercase tracking-[0.16em] text-lime-100">
          {running ? "Running" : "Typing"}
        </p>
        <h2 className="min-w-0 flex-1 truncate text-lg font-extrabold tracking-tight text-white sm:text-xl">
          {topic}
        </h2>
      </header>

      <div className="mt-2 grid min-h-0 flex-1 gap-2 md:grid-cols-[minmax(0,1.15fr)_minmax(240px,0.85fr)]">
        <div className="flex min-h-0 flex-col overflow-hidden rounded-2xl border border-cyan-200/20 bg-[#07111f]/92">
          <ReelCodePanel
            code={revealed || " "}
            filename={filename}
            highlight={activeHighlight}
            caret={typing && revealed.length < code.length}
          />
          {running ? (
            <div className="shrink-0 border-t border-amber-300/25 bg-black/55 px-3 py-2">
              <div className="mb-1 flex items-center justify-between gap-2">
                <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-amber-300">
                  {beat ? `Debug · ${beat.label}` : "Debug"}
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
              <div className="max-h-24 overflow-hidden font-mono text-[12px] leading-4 text-zinc-200">
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
                  <p className="max-h-16 overflow-y-auto whitespace-pre-wrap text-red-300">
                    {runError || scene.stderr}
                  </p>
                ) : null}
              </div>
            </div>
          ) : null}
        </div>

        <aside className="flex min-h-0 flex-col overflow-hidden rounded-2xl border border-lime-200/20 bg-[#0b140c]/92 p-3">
          <div className="flex shrink-0 items-center gap-3">
            <TalkingByteAvatar
              speaking={playing}
              narration={narration}
              currentTime={currentTime}
              duration={duration}
              size="lg"
            />
            <div className="min-w-0">
              <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-lime-300">
                {running ? "While it runs" : "While it types"}
              </p>
              <p className="text-xs text-zinc-400">Pavi explains this line</p>
            </div>
          </div>
          <div className="mt-3 min-h-0 flex-1 overflow-y-auto">
            <KaraokeCaption
              text={explainBody}
              currentTime={currentTime}
              duration={duration}
              cueStart={running && beat ? beat.start : karaokeStart}
              cueEnd={running && beat ? beat.end : karaokeEnd}
              segments={running ? [] : scene.segments}
            />
            {running && karaokeText && beat?.description && karaokeText !== beat.description ? (
              <p className="mt-3 text-sm leading-6 text-zinc-200">{karaokeText}</p>
            ) : null}
          </div>
        </aside>
      </div>
    </div>
  );
}
