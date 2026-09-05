"use client";

import { useEffect, useMemo, useRef } from "react";
import { TalkingByteAvatar } from "@/components/tutor/TalkingByteAvatar";
import { ReelCodePanel } from "@/components/player/ReelCodePanel";
import { sourceFilename } from "@/lib/language";
import { beatHighlight, reelBeatAt, reelBeats } from "@/lib/reelDebugSync";
import { isPosterScene, reelCta } from "@/lib/reelCta";
import { infoBulletAt, playInfoBulletBlip } from "@/lib/infoReelAnim";
import { displayTopic, stripDurationNoise } from "@/lib/reelHeadlines";
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
  terminalLines = [],
  runError,
  iterations = [],
  sceneIndex = 0,
  sceneCount = 4,
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
  sceneIndex?: number;
  sceneCount?: number;
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
  const printed = (beat?.output?.length ? beat.output : terminalLines) ?? [];
  const latest = beat?.latest ?? (printed.length ? printed[printed.length - 1] : undefined);
  const narration = stripDurationNoise(scene.narration || caption);
  const spokenCaption = stripDurationNoise(caption);
  const showConsole = running || Boolean(runError || scene.stderr);
  const topic = displayTopic(lesson.topic);
  const poster = isPosterScene(scene.type);
  const thumb = lesson.thumbnail_url || "";
  const cta = reelCta(lesson, scene);
  const progress = duration > 0 ? Math.min(1, Math.max(0, currentTime / duration)) : 0;
  const isConcept = scene.type === "concept" || ((scene.type === "code" || scene.type === "execution") && (!(code || "").trim() || lesson.requires_code === false));
  const infoAnim = useMemo(
    () => (isConcept ? infoBulletAt(scene.bullets || [], currentTime, duration) : null),
    [isConcept, scene.bullets, currentTime, duration],
  );
  const lastBlip = useRef(-1);
  useEffect(() => {
    lastBlip.current = -1;
  }, [scene.type, sceneIndex]);
  useEffect(() => {
    if (!playing || !infoAnim || infoAnim.visibleCount === 0) return;
    if (infoAnim.active === lastBlip.current) return;
    lastBlip.current = infoAnim.active;
    playInfoBulletBlip();
  }, [playing, infoAnim?.active, infoAnim?.visibleCount]);

  return (
    <div className="reel-stage relative flex h-full max-h-full w-auto max-w-full aspect-[9/16] flex-col overflow-hidden rounded-[2rem] border border-white/12 px-3 pb-3 pt-5 shadow-[0_30px_80px_rgba(0,0,0,0.55)]">
      {poster && thumb ? (
        <img src={thumb} alt="" className="pointer-events-none absolute inset-0 z-0 h-full w-full object-cover" />
      ) : null}
      <div className="pointer-events-none absolute inset-x-0 top-0 z-[1] h-28 bg-gradient-to-b from-black/70 to-transparent" />
      <div className="pointer-events-none absolute inset-x-0 bottom-0 z-[1] h-52 bg-gradient-to-t from-black/80 to-transparent" />
      <div className="reel-stage-vignette pointer-events-none absolute inset-0 z-[1]" />

      <div className="relative z-20 mt-1 flex gap-1 px-1">
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

      <div className="pointer-events-none absolute right-2 top-11 z-30 drop-shadow-[0_8px_18px_rgba(0,0,0,0.55)]">
        <img src="/techshala-logo.png" alt="TECHSHALA by Pavi" className="h-[5.5rem] w-auto" />
      </div>

      <div className="relative z-20 mt-3 flex items-center gap-2 px-1">
        <span className="text-sm font-semibold text-white">{cta.handle}</span>
        <span className="rounded-full bg-amber-400 px-2.5 py-0.5 text-[11px] font-extrabold uppercase tracking-wide text-zinc-950">
          {cta.follow}
        </span>
      </div>

      {poster ? (
        <div className="relative z-10 flex min-h-0 flex-1 flex-col justify-end px-4 pb-2">
          {scene.type === "summary" ? (
            <div className="rounded-2xl border border-white/10 bg-black/70 px-4 py-3 text-center backdrop-blur-md">
              <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-amber-300">Save this</p>
              <p className="mt-1 line-clamp-2 text-lg font-extrabold leading-6 text-white">{cta.endLine}</p>
              <p className="reel-cta-pulse mt-3 inline-flex rounded-full bg-amber-400 px-5 py-2 text-sm font-extrabold text-zinc-950">
                {cta.endAction}
              </p>
              <p className="mt-2 line-clamp-2 text-sm font-medium text-zinc-100">{cta.comment}</p>
            </div>
          ) : thumb ? (
            <div className="h-full" />
          ) : (
            <div className="flex flex-1 flex-col items-center justify-center text-center">
              <p className="inline-flex rounded-full border border-cyan-200/30 bg-cyan-300/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-cyan-100">
                {lesson.language}
              </p>
              <h2 className="mt-3 line-clamp-3 text-[1.85rem] font-extrabold leading-9 tracking-tight text-white">
                {topic}
              </h2>
            </div>
          )}
        </div>
      ) : isConcept ? (
        <>
          <div className="pointer-events-none absolute inset-0 z-[2] overflow-hidden">
            <div className="info-orb bg-violet-500/45" style={{ width: 190, height: 190, left: -48, top: 110 }} />
            <div
              className="info-orb bg-fuchsia-400/30"
              style={{ width: 150, height: 150, right: -28, top: 260, animationDelay: "1.2s" }}
            />
            <div
              className="info-orb bg-cyan-400/25"
              style={{ width: 120, height: 120, left: 36, bottom: 250, animationDelay: "2.4s" }}
            />
          </div>
          <header className="relative z-10 shrink-0 px-1 pt-2 text-center">
            <p className="info-step-chip inline-flex rounded-full border border-violet-200/30 bg-violet-300/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-violet-100">
              Explain
            </p>
            <h2 className="mt-2 line-clamp-2 text-xl font-semibold leading-6 tracking-tight text-white">{topic}</h2>
          </header>
          <div className="relative z-10 flex min-h-0 flex-1 flex-col items-stretch justify-center py-2">
            <div className="flex max-h-full min-h-0 flex-col gap-2 overflow-y-auto rounded-2xl border border-violet-200/20 bg-[#12071f]/92 p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]">
              {(scene.bullets || []).length ? (
                (scene.bullets || []).map((item, index) => {
                  const visible = (infoAnim?.visibleCount ?? 0) > index;
                  const active = infoAnim?.active === index;
                  return (
                    <p
                      key={`${index}-${item}`}
                      className={cn(
                        "info-bullet rounded-xl border border-white/10 bg-black/35 px-3 py-2 text-sm font-medium leading-5 text-zinc-100",
                        visible && "is-visible",
                        active && "is-active",
                      )}
                    >
                      <span className="mr-2 inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-violet-400/25 px-1.5 text-[10px] font-bold text-violet-100">
                        {index + 1}
                      </span>
                      {item}
                    </p>
                  );
                })
              ) : (
                <p className="text-sm leading-6 text-zinc-200">{narration}</p>
              )}
            </div>
          </div>
        </>
      ) : (
        <>
          <header className="relative z-10 shrink-0 px-1 pt-2 text-center">
            <p className="inline-flex rounded-full border border-cyan-200/30 bg-cyan-300/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-cyan-100">
              {lesson.language}
            </p>
            <h2 className="mt-2 line-clamp-2 text-xl font-semibold leading-6 tracking-tight text-white">{topic}</h2>
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
                      <p className="text-zinc-500">waiting for print… (sandbox has no output yet — start code-runner on :8090)</p>
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
                      <p className="max-h-20 overflow-y-auto whitespace-pre-wrap text-red-300">
                        {runError || scene.stderr}
                      </p>
                    ) : null}
                  </div>
                </div>
              ) : null}
            </div>
          </div>
        </>
      )}

      <div className="relative z-10 flex shrink-0 items-end gap-3">
        <TalkingByteAvatar
          speaking={playing}
          narration={narration}
          currentTime={currentTime}
          duration={duration}
          size="lg"
        />
        <div className="mb-1 min-w-0 flex-1 rounded-2xl border border-white/10 bg-black/60 px-3 py-2.5 backdrop-blur-md">
          <p className="line-clamp-3 text-sm font-medium leading-5 text-white">{spokenCaption}</p>
        </div>
      </div>
    </div>
  );
}
