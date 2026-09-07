"use client";

import { useEffect, useMemo, useRef } from "react";
import { TalkingByteAvatar } from "@/components/tutor/TalkingByteAvatar";
import { KaraokeCaption } from "@/components/player/Caption";
import { buildCues, cueAt } from "@/lib/narrationSync";
import { ReelCodePanel } from "@/components/player/ReelCodePanel";
import { HashMapBoard } from "@/components/player/HashMapBoard";
import { MechanismBoard } from "@/components/player/MechanismBoard";
import type { HashMapVisual } from "@/types/lesson";
import { boardStateFromSteps } from "@/lib/hashmapPhase";
import { sourceFilename } from "@/lib/language";
import { beatHighlight, reelBeatAt, reelBeats } from "@/lib/reelDebugSync";
import { isPosterScene, reelCta } from "@/lib/reelCta";
import { boardKindLabel, isExplainMotionLesson, lessonExplainedTopicDetails, lessonExplainedTopics, synthesizeBoardSteps } from "@/lib/explainerVisuals";
import { beatsFromSegments, infoBulletAt, infoBulletAtBeats, playInfoBulletBlip } from "@/lib/infoReelAnim";
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
  // Same cue clock as LessonPlayer highlights — karaoke must use this window, not the whole scene.
  const narrationCues = useMemo(() => buildCues(scene, duration), [scene, duration]);
  const karaokeCue = cueAt(narrationCues, currentTime);
  const karaokeText = stripDurationNoise(karaokeCue?.text || spokenCaption || scene.narration || "");
  const karaokeStart = karaokeCue?.start ?? 0;
  const karaokeEnd = karaokeCue?.end ?? Math.max(duration, karaokeStart + 0.5);
  const showConsole = running || Boolean(runError || scene.stderr);
  const topic = displayTopic(lesson.topic);
  const explainMotion = isExplainMotionLesson(lesson);
  // Code shorts keep static poster intros/summaries; explainer/info always get motion boards.
  const poster = isPosterScene(scene.type) && !explainMotion;
  const thumb = lesson.thumbnail_url || "";
  const cta = reelCta(lesson, scene);
  const progress = duration > 0 ? Math.min(1, Math.max(0, currentTime / duration)) : 0;
  const isExplainer =
    lesson.reel_mode === "explainer" ||
    (lesson.reel_mode !== "info" && Boolean(scene.diagram_steps && scene.diagram_steps.length));
  const isConcept =
    scene.type === "concept" ||
    (explainMotion && (scene.type === "intro" || scene.type === "summary")) ||
    ((scene.type === "code" || scene.type === "execution") &&
      (!(code || "").trim() || lesson.requires_code === false));
  const diagramSteps = useMemo(() => {
    // Prefer planner diagram_steps/bullets; else synthesize from visual/segments/narration
    // so kind:none never leaves a blank stage on explainer/info.
    return synthesizeBoardSteps(scene, lesson);
  }, [scene, lesson]);
  const explainedTopics = useMemo(
    () => (explainMotion || isExplainMotionLesson(lesson) ? lessonExplainedTopics(lesson) : []),
    [explainMotion, lesson],
  );
  const explainedTopicDetails = useMemo(
    () => (explainMotion || isExplainMotionLesson(lesson) ? lessonExplainedTopicDetails(lesson) : []),
    [explainMotion, lesson],
  );
  const summaryRecap = scene.type === "summary" && explainedTopics.length > 0;
  const summaryTakeaways = useMemo(
    () => (scene.takeaways || []).map((t) => String(t || "").trim()).filter(Boolean),
    [scene.takeaways],
  );
  const hashmapVisual = useMemo((): HashMapVisual | null => {
    const raw = scene.visual_diagram;
    if (raw && raw.kind === "hashmap") return raw;
    const blob = `${lesson.topic || ""} ${topic || ""}`.toLowerCase();
    if (isExplainer && /hash\s*map|hashtable|hash\s*table/.test(blob)) {
      return {
        kind: "hashmap",
        capacity: 8,
        init_code: "Map<String,Integer> map = new HashMap<>();",
        setup_lines: [],
        puts: [
          { code: 'map.put("Mia",95)', key: "Mia", value: "95", hash_bits: "1010", bucket: 2, color: "orange" },
          { code: 'map.put("Leo",88)', key: "Leo", value: "88", hash_bits: "0101", bucket: 5, color: "blue" },
          { code: 'map.put("Zoe",92)', key: "Zoe", value: "92", hash_bits: "1010", bucket: 2, color: "green" },
        ],
        node_fields: ["key", "value", "hash", "next"],
      };
    }
    return null;
  }, [scene.visual_diagram, lesson.topic, topic, isExplainer]);
  const putTitles = useMemo(
    () => (hashmapVisual?.puts || []).map((p) => p.code || p.key).filter(Boolean),
    [hashmapVisual],
  );
  const stepTitles = useMemo(() => diagramSteps.map((s) => s.title), [diagramSteps]);
  // Prefer diagram phase titles when hashmap explainer has diagram_steps; else put codes
  const syncTitles =
    summaryRecap
      ? explainedTopics
      : hashmapVisual && diagramSteps.length
        ? stepTitles
        : putTitles.length
          ? putTitles
          : isExplainer
            ? stepTitles
            : scene.bullets || [];
  const infoAnim = useMemo(() => {
    if (!isConcept) return null;
    const segs = scene.segments || [];
    // Summary recap: reveal every explained topic across the end-card window.
    if (summaryRecap) {
      return infoBulletAt(explainedTopics, currentTime, duration);
    }
    // When diagram step count differs from narration segments, equal-split steps across
    // the real clip duration so every phase (e.g. 5 board steps) still appears on screen.
    if (diagramSteps.length >= 2 && Math.abs(diagramSteps.length - segs.length) >= 1) {
      return infoBulletAt(stepTitles, currentTime, duration);
    }
    // Otherwise lock phases to narration segment clocks (rescaled to clip duration).
    if ((hashmapVisual || diagramSteps.length) && segs.length >= 2) {
      const beats = beatsFromSegments(segs, duration);
      return infoBulletAtBeats(beats, currentTime);
    }
    return infoBulletAt(syncTitles, currentTime, duration);
  }, [
    isConcept,
    summaryRecap,
    explainedTopics,
    hashmapVisual,
    diagramSteps.length,
    stepTitles,
    scene.segments,
    syncTitles,
    currentTime,
    duration,
  ]);
  const boardState = useMemo(() => {
    if (!diagramSteps.length) return null;
    const putCount = hashmapVisual?.puts?.length ?? 0;
    return boardStateFromSteps(diagramSteps, infoAnim?.active ?? 0, putCount);
  }, [hashmapVisual, diagramSteps, infoAnim?.active]);
  const putProgress = useMemo(() => {
    if (boardState) {
      // Blend suggested phase progress with intra-beat timing for slide-in feel
      if (!infoAnim || !infoAnim.beats.length) return boardState.progressHint;
      const beat = infoAnim.beats[Math.max(0, Math.min(infoAnim.active, infoAnim.beats.length - 1))];
      if (!beat) return boardState.progressHint;
      const span = Math.max(0.05, beat.end - beat.start);
      const local = Math.max(0, Math.min(1, (currentTime - beat.start) / span));
      if (boardState.phaseKind === "tree") return 1;
      if (boardState.phaseKind === "hash" || boardState.phaseKind === "index") {
        return Math.min(boardState.progressHint, 0.15 + local * 0.2);
      }
      return Math.max(boardState.progressHint * 0.55, local);
    }
    if (!infoAnim || !infoAnim.beats.length) return 1;
    const beat = infoAnim.beats[Math.max(0, Math.min(infoAnim.active, infoAnim.beats.length - 1))];
    if (!beat) return 1;
    const span = Math.max(0.05, beat.end - beat.start);
    return Math.max(0, Math.min(1, (currentTime - beat.start) / span));
  }, [boardState, infoAnim, currentTime]);
  const activePutIndex = boardState ? boardState.activePutIndex : (infoAnim?.active ?? 0);
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
    <div className="reel-stage relative flex h-full max-h-full w-auto max-w-full aspect-[9/16] flex-col overflow-hidden rounded-[2rem] border border-white/12 px-3 pb-4 pt-4 shadow-[0_30px_80px_rgba(0,0,0,0.55)]">
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
            <div
              className={cn("info-orb", isExplainer ? "bg-cyan-500/45" : "bg-violet-500/45")}
              style={{ width: 190, height: 190, left: -48, top: 110 }}
            />
            <div
              className={cn("info-orb", isExplainer ? "bg-amber-400/30" : "bg-fuchsia-400/30")}
              style={{ width: 150, height: 150, right: -28, top: 260, animationDelay: "1.2s" }}
            />
            <div
              className={cn("info-orb", isExplainer ? "bg-teal-400/25" : "bg-cyan-400/25")}
              style={{ width: 120, height: 120, left: 36, bottom: 250, animationDelay: "2.4s" }}
            />
          </div>
          <header className="relative z-10 shrink-0 px-1 pt-2 text-center">
            <p
              className={cn(
                "info-step-chip inline-flex rounded-full border px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em]",
                isExplainer || scene.type === "intro" || scene.type === "summary"
                  ? "border-cyan-200/30 bg-cyan-300/10 text-cyan-100"
                  : "border-violet-200/30 bg-violet-300/10 text-violet-100",
              )}
            >
              {summaryRecap ? "Recap" : explainMotion ? boardKindLabel(scene) : isExplainer ? "Explainer" : "Explain"}
            </p>
            {scene.type === "intro" && currentTime < 2.6 && !diagramSteps[0]?.title ? (
              <p className="reel-cta-pulse mt-2 inline-flex rounded-full bg-amber-400 px-4 py-1.5 text-sm font-extrabold uppercase tracking-wide text-zinc-950">
                Wait for it…
              </p>
            ) : null}
            <h2 className="mt-2 line-clamp-2 text-2xl font-extrabold leading-7 tracking-tight text-white">{topic}</h2>
            {summaryRecap ? (
              <p className="mt-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-amber-200/90">
                What we covered · {Math.min(infoAnim?.visibleCount ?? 1, explainedTopics.length)}/{explainedTopics.length}
              </p>
            ) : scene.type === "summary" && summaryTakeaways.length ? (
              <p className="mt-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-amber-200/90">
                End card · {Math.min((infoAnim?.visibleCount ?? 1), summaryTakeaways.length)} reveals
              </p>
            ) : null}
          </header>
      <div className="relative z-20 mt-2 flex shrink-0 items-center gap-3 px-1">
        <TalkingByteAvatar
          speaking={playing}
          narration={narration}
          currentTime={currentTime}
          duration={duration}
          size="xl"
        />
        <KaraokeCaption
          text={karaokeText}
          currentTime={currentTime}
          duration={duration}
          cueStart={karaokeStart}
          cueEnd={karaokeEnd}
          segments={scene.segments}
        />
      </div>
          <div className="relative z-10 flex min-h-0 flex-1 flex-col items-stretch justify-center py-1">
            {summaryRecap ? (
              <div className="flex max-h-full min-h-0 flex-col gap-2 overflow-y-auto rounded-2xl border border-cyan-200/25 bg-[#031018]/94 p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]">
                <p className="text-center text-[11px] font-semibold uppercase tracking-[0.24em] text-cyan-200/90">
                  What we covered
                </p>
                <div className="flex min-h-0 flex-1 flex-col gap-1.5">
                  {explainedTopics.map((item, index) => {
                    const visible = (infoAnim?.visibleCount ?? 0) > index;
                    const active = infoAnim?.active === index;
                    const detail = explainedTopicDetails[index] || "";
                    return (
                      <div
                        key={`recap-${index}-${item}`}
                        className={cn(
                          "info-bullet flex items-start gap-3 rounded-xl border border-white/10 bg-black/40 px-3 py-2.5 text-zinc-100",
                          visible && "is-visible",
                          active && "is-active",
                        )}
                      >
                        <span
                          className={cn(
                            "mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[11px] font-bold",
                            visible
                              ? "bg-emerald-400/25 text-emerald-100"
                              : "bg-cyan-400/25 text-cyan-50",
                          )}
                          aria-hidden
                        >
                          {visible ? "✓" : index + 1}
                        </span>
                        <span className="min-w-0 flex-1">
                          <span className="block text-[14px] font-semibold leading-5 tracking-normal">
                            {item}
                          </span>
                          {detail ? (
                            <span className="mt-0.5 block text-[11px] font-medium leading-4 text-cyan-100/75">
                              {detail}
                            </span>
                          ) : null}
                        </span>
                      </div>
                    );
                  })}
                </div>
                {summaryTakeaways.length ? (
                  <p className="mt-1 line-clamp-2 text-center text-[11px] font-medium leading-4 text-amber-100/80">
                    {summaryTakeaways.slice(0, 2).join(" · ")}
                  </p>
                ) : (
                  <p className="mt-1 text-center text-[11px] font-semibold uppercase tracking-[0.18em] text-amber-200/80">
                    {cta.endAction}
                  </p>
                )}
              </div>
            ) : isExplainer && hashmapVisual ? (
              <HashMapBoard
                visual={hashmapVisual}
                activePutIndex={activePutIndex}
                progress={putProgress}
                topic={topic}
                phaseLabel={boardState?.phaseLabel}
                phaseExample={boardState?.phaseExample}
                phaseKind={boardState?.phaseKind}
              />
            ) : isExplainer && diagramSteps.length ? (
              <MechanismBoard
                steps={diagramSteps}
                active={infoAnim?.active ?? 0}
                progress={putProgress}
                topic={topic}
                phaseLabel={boardState?.phaseLabel}
                phaseExample={boardState?.phaseExample}
              />
            ) : (
            <div
              className={cn(
                "flex max-h-full min-h-0 flex-col gap-2 overflow-y-auto rounded-2xl border p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]",
                "border-violet-200/20 bg-[#12071f]/92",
              )}
            >
              {(diagramSteps.length ? diagramSteps.map((s) => s.title) : scene.bullets || []).length ? (
                (diagramSteps.length ? diagramSteps.map((s) => s.title) : scene.bullets || []).map((item, index) => {
                  const visible = (infoAnim?.visibleCount ?? 0) > index;
                  const active = infoAnim?.active === index;
                  return (
                    <p
                      key={`${index}-${item}`}
                      className={cn(
                        "info-bullet rounded-xl border border-white/10 bg-black/35 px-3.5 py-2.5 text-[15px] font-semibold leading-5 text-zinc-100",
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
            )}
          </div>
        </>
      ) : (
        <>
          <header className="relative z-10 shrink-0 px-1 pt-2 text-center">
            <p className="inline-flex rounded-full border border-cyan-200/30 bg-cyan-300/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-cyan-100">
              {lesson.language}
            </p>
            <h2 className="mt-2 line-clamp-2 text-2xl font-extrabold leading-7 tracking-tight text-white">{topic}</h2>
          </header>
      <div className="relative z-20 mt-2 flex shrink-0 items-center gap-3 px-1">
        <TalkingByteAvatar
          speaking={playing}
          narration={narration}
          currentTime={currentTime}
          duration={duration}
          size="xl"
        />
        <KaraokeCaption
          text={karaokeText}
          currentTime={currentTime}
          duration={duration}
          cueStart={karaokeStart}
          cueEnd={karaokeEnd}
          segments={scene.segments}
        />
      </div>
          <div className="relative z-10 flex min-h-0 flex-1 flex-col items-stretch justify-center py-1">
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
                  <div className="max-h-28 overflow-hidden font-mono text-[12px] leading-4 text-zinc-200">
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

    </div>
  );
}
