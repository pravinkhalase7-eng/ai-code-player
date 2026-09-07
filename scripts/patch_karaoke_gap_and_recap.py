#!/usr/bin/env python3
"""Widen karaoke word gaps + add summary 'What we covered' recap checklist.

Task 1: Caption.tsx / globals.css / reelExport karaoke spacing.
Task 2: lessonExplainedTopics helper + ReelStage/reelExport summary recap UI.
No git commit.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder")


def must_replace(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"MISSING block in {path.name}: {label}")
    if text.count(old) != 1:
        raise SystemExit(f"AMBIGUOUS ({text.count(old)}x) in {path.name}: {label}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"ok {path.relative_to(ROOT)} :: {label}")


def patch_caption() -> None:
    path = ROOT / "frontend/components/player/Caption.tsx"
    old = '''      <p className="flex flex-wrap content-center gap-x-1.5 gap-y-1 text-[15px] font-semibold leading-6 tracking-tight text-zinc-300 sm:text-base">
        {windowWords.length ? (
          windowWords.map((word) => {
            const isActive = word.index === active;
            const isPast = word.index < active;
            return (
              <span
                key={`${word.index}-${word.text}`}
                className={cn(
                  "karaoke-word inline-block transition-all duration-100",
                  isActive && "karaoke-word-active",
                  isPast && !isActive && "text-white",
                  !isPast && !isActive && "text-zinc-500",
                )}
              >
                {word.text}
              </span>
            );
          })
        ) : (
          <span className="text-white">{text}</span>
        )}
      </p>'''
    new = '''      <p className="flex flex-wrap content-center gap-x-2.5 gap-y-1.5 text-[15px] font-semibold leading-6 tracking-normal text-zinc-300 sm:text-base">
        {windowWords.length ? (
          windowWords.map((word) => {
            const isActive = word.index === active;
            const isPast = word.index < active;
            return (
              <span
                key={`${word.index}-${word.text}`}
                className={cn(
                  "karaoke-word inline-block px-0.5 mx-px transition-all duration-100",
                  isActive && "karaoke-word-active",
                  isPast && !isActive && "text-white",
                  !isPast && !isActive && "text-zinc-500",
                )}
              >
                {word.text}
              </span>
            );
          })
        ) : (
          <span className="text-white">{text}</span>
        )}
      </p>'''
    must_replace(path, old, new, "karaoke gap/tracking/padding")


def patch_globals() -> None:
    path = ROOT / "frontend/app/globals.css"
    old = '''/* Karaoke caption words (audio-synced) */
.karaoke-word {
  transform: translateY(0) scale(1);
}
.karaoke-word-active {
  color: #fde68a !important;
  text-shadow: 0 0 18px rgba(251, 191, 36, 0.55);
  transform: translateY(-1px) scale(1.12);
  font-weight: 800;
  animation: karaoke-pop 0.22s cubic-bezier(0.22, 1, 0.36, 1);
}
@keyframes karaoke-pop {
  0% { transform: translateY(4px) scale(0.92); opacity: 0.7; }
  100% { transform: translateY(-1px) scale(1.12); opacity: 1; }
}'''
    new = '''/* Karaoke caption words (audio-synced) */
.karaoke-word {
  transform: translateY(0) scale(1);
  transform-origin: center bottom;
  padding-inline: 0.12em;
}
.karaoke-word-active {
  color: #fde68a !important;
  text-shadow: 0 0 18px rgba(251, 191, 36, 0.55);
  transform: translateY(-1px) scale(1.07);
  font-weight: 800;
  animation: karaoke-pop 0.22s cubic-bezier(0.22, 1, 0.36, 1);
}
@keyframes karaoke-pop {
  0% { transform: translateY(4px) scale(0.94); opacity: 0.7; }
  100% { transform: translateY(-1px) scale(1.07); opacity: 1; }
}'''
    must_replace(path, old, new, "karaoke scale/origin/padding")


def patch_explainer_visuals() -> None:
    path = ROOT / "frontend/lib/explainerVisuals.ts"
    old = '''export function boardKindLabel(scene: LessonScene): string {
  if (scene.type === "intro") return "Hook";
  if (scene.type === "summary") return "Takeaway";
  return "Explainer";
}
'''
    new = '''export function boardKindLabel(scene: LessonScene): string {
  if (scene.type === "intro") return "Hook";
  if (scene.type === "summary") return "Takeaway";
  return "Explainer";
}

/** Deduped topic titles covered by concept scenes — for summary "What we covered". */
export function lessonExplainedTopics(lesson: Lesson): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  const push = (raw: string) => {
    const title = cleanBoardTitle(String(raw || "").trim());
    if (!title) return;
    const key = normalizeForCompare(title);
    if (!key || seen.has(key)) return;
    seen.add(key);
    out.push(clip(title, 56));
  };

  const concepts = (lesson.scenes || []).filter((s) => s.type === "concept");

  let fromDiagram = false;
  for (const scene of concepts) {
    for (const step of scene.diagram_steps || []) {
      const title = String(step?.title || "").trim();
      if (title) {
        push(title);
        fromDiagram = true;
      }
    }
  }
  if (fromDiagram && out.length) return out;

  for (const scene of concepts) {
    for (const b of scene.bullets || []) push(String(b || ""));
    for (const c of scene.visual?.callouts || []) push(String(c || ""));
  }
  if (out.length) return out;

  for (const scene of concepts) {
    for (const step of synthesizeBoardSteps(scene, lesson)) {
      push(step.title);
    }
  }
  return out;
}
'''
    must_replace(path, old, new, "lessonExplainedTopics helper")


def patch_reel_stage() -> None:
    path = ROOT / "frontend/components/player/ReelStage.tsx"
    old_import = 'import { boardKindLabel, isExplainMotionLesson, synthesizeBoardSteps } from "@/lib/explainerVisuals";'
    new_import = 'import { boardKindLabel, isExplainMotionLesson, lessonExplainedTopics, synthesizeBoardSteps } from "@/lib/explainerVisuals";'
    must_replace(path, old_import, new_import, "import lessonExplainedTopics")

    old_steps = '''  const diagramSteps = useMemo(() => {
    // Prefer planner diagram_steps/bullets; else synthesize from visual/segments/narration
    // so kind:none never leaves a blank stage on explainer/info.
    return synthesizeBoardSteps(scene, lesson);
  }, [scene, lesson]);
'''
    new_steps = '''  const diagramSteps = useMemo(() => {
    // Prefer planner diagram_steps/bullets; else synthesize from visual/segments/narration
    // so kind:none never leaves a blank stage on explainer/info.
    return synthesizeBoardSteps(scene, lesson);
  }, [scene, lesson]);
  const explainedTopics = useMemo(
    () => (explainMotion || isExplainMotionLesson(lesson) ? lessonExplainedTopics(lesson) : []),
    [explainMotion, lesson],
  );
  const summaryRecap = scene.type === "summary" && explainedTopics.length > 0;
  const summaryTakeaways = useMemo(
    () => (scene.takeaways || []).map((t) => String(t || "").trim()).filter(Boolean),
    [scene.takeaways],
  );
'''
    must_replace(path, old_steps, new_steps, "explainedTopics memos")

    # Sync infoAnim to recap topics on summary
    old_sync = '''  const stepTitles = useMemo(() => diagramSteps.map((s) => s.title), [diagramSteps]);
  // Prefer diagram phase titles when hashmap explainer has diagram_steps; else put codes
  const syncTitles =
    hashmapVisual && diagramSteps.length
      ? stepTitles
      : putTitles.length
        ? putTitles
        : isExplainer
          ? stepTitles
          : scene.bullets || [];
'''
    new_sync = '''  const stepTitles = useMemo(() => diagramSteps.map((s) => s.title), [diagramSteps]);
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
'''
    must_replace(path, old_sync, new_sync, "syncTitles summary recap")

    old_anim = '''  const infoAnim = useMemo(() => {
    if (!isConcept) return null;
    const segs = scene.segments || [];
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
    hashmapVisual,
    diagramSteps.length,
    stepTitles,
    scene.segments,
    syncTitles,
    currentTime,
    duration,
  ]);
'''
    new_anim = '''  const infoAnim = useMemo(() => {
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
'''
    must_replace(path, old_anim, new_anim, "infoAnim summary recap")

    old_header = '''            {scene.type === "summary" && (scene.takeaways || []).length ? (
              <p className="mt-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-amber-200/90">
                End card · {Math.min((infoAnim?.visibleCount ?? 1), (scene.takeaways || []).length)} reveals
              </p>
            ) : null}
'''
    new_header = '''            {summaryRecap ? (
              <p className="mt-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-amber-200/90">
                What we covered · {Math.min(infoAnim?.visibleCount ?? 1, explainedTopics.length)}/{explainedTopics.length}
              </p>
            ) : scene.type === "summary" && summaryTakeaways.length ? (
              <p className="mt-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-amber-200/90">
                End card · {Math.min((infoAnim?.visibleCount ?? 1), summaryTakeaways.length)} reveals
              </p>
            ) : null}
'''
    must_replace(path, old_header, new_header, "summary header chip")

    old_board = '''          <div className="relative z-10 flex min-h-0 flex-1 flex-col items-stretch justify-center py-1">
            {isExplainer && hashmapVisual ? (
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
'''
    new_board = '''          <div className="relative z-10 flex min-h-0 flex-1 flex-col items-stretch justify-center py-1">
            {summaryRecap ? (
              <div className="flex max-h-full min-h-0 flex-col gap-2 overflow-y-auto rounded-2xl border border-cyan-200/25 bg-[#031018]/94 p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]">
                <p className="text-center text-[11px] font-semibold uppercase tracking-[0.24em] text-cyan-200/90">
                  What we covered
                </p>
                <div className="flex min-h-0 flex-1 flex-col gap-1.5">
                  {explainedTopics.map((item, index) => {
                    const visible = (infoAnim?.visibleCount ?? 0) > index;
                    const active = infoAnim?.active === index;
                    return (
                      <p
                        key={`recap-${index}-${item}`}
                        className={cn(
                          "info-bullet rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-[14px] font-semibold leading-5 text-zinc-100",
                          visible && "is-visible",
                          active && "is-active",
                        )}
                      >
                        <span className="mr-2 inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-cyan-400/25 px-1.5 text-[10px] font-bold text-cyan-50">
                          {visible ? "✓" : index + 1}
                        </span>
                        {item}
                      </p>
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
'''
    must_replace(path, old_board, new_board, "summary recap checklist UI")


def patch_reel_export() -> None:
    path = ROOT / "frontend/lib/reelExport.ts"
    old_import = 'import { isExplainMotionLesson, synthesizeBoardSteps } from "@/lib/explainerVisuals";'
    new_import = 'import { isExplainMotionLesson, lessonExplainedTopics, synthesizeBoardSteps } from "@/lib/explainerVisuals";'
    must_replace(path, old_import, new_import, "import lessonExplainedTopics")

    old_karaoke = '''  const karaokeWords = buildKaraokeWords(caption, duration, {
    cueStart: cue?.start ?? 0,
    cueEnd: cue?.end ?? duration,
    segments: scene.segments || [],
  });
  const active = activeWordIndex(karaokeWords, elapsed);
  const windowWords = karaokeWindow(karaokeWords, Math.max(0, active), 12);
  ctx.font = "700 22px ui-sans-serif, system-ui";
  let kx = boxX + 16;
  let ky = boxY + 40;
  const maxX = boxX + boxW - 16;
  const lineH = 28;
  for (const word of windowWords) {
    const metrics = ctx.measureText(word.text + " ");
    if (kx + metrics.width > maxX) {
      kx = boxX + 16;
      ky += lineH;
      if (ky > boxY + boxH - 12) break;
    }
    const isActive = word.index === active;
    const isPast = word.index < active;
    ctx.fillStyle = isActive ? "#fde68a" : isPast ? "#ffffff" : "#a1a1aa";
    if (isActive) {
      ctx.save();
      ctx.shadowColor = "rgba(251,191,36,0.55)";
      ctx.shadowBlur = 16;
      ctx.fillText(word.text, kx, ky);
      ctx.restore();
    } else {
      ctx.fillText(word.text, kx, ky);
    }
    kx += metrics.width;
  }
'''
    new_karaoke = '''  const karaokeWords = buildKaraokeWords(caption, duration, {
    cueStart: cue?.start ?? 0,
    cueEnd: cue?.end ?? duration,
    segments: scene.segments || [],
  });
  const active = activeWordIndex(karaokeWords, elapsed);
  const windowWords = karaokeWindow(karaokeWords, Math.max(0, active), 12);
  ctx.font = "700 22px ui-sans-serif, system-ui";
  let kx = boxX + 16;
  let ky = boxY + 40;
  const maxX = boxX + boxW - 16;
  const lineH = 30;
  // Match UI: gap-x-2.5 (~10px) + px-0.5 padding so scaled active words do not collide.
  const wordGap = 10;
  const wordPad = 3;
  for (const word of windowWords) {
    const textW = ctx.measureText(word.text).width;
    const advance = textW + wordPad * 2 + wordGap;
    if (kx + advance > maxX) {
      kx = boxX + 16;
      ky += lineH;
      if (ky > boxY + boxH - 12) break;
    }
    const isActive = word.index === active;
    const isPast = word.index < active;
    ctx.fillStyle = isActive ? "#fde68a" : isPast ? "#ffffff" : "#a1a1aa";
    const drawX = kx + wordPad;
    if (isActive) {
      ctx.save();
      ctx.shadowColor = "rgba(251,191,36,0.55)";
      ctx.shadowBlur = 16;
      // Mild scale (~1.07) from bottom-center without overlapping neighbors.
      ctx.translate(drawX + textW / 2, ky);
      ctx.scale(1.07, 1.07);
      ctx.fillText(word.text, -textW / 2, 0);
      ctx.restore();
    } else {
      ctx.fillText(word.text, drawX, ky);
    }
    kx += advance;
  }
'''
    must_replace(path, old_karaoke, new_karaoke, "karaoke canvas spacing")

    # Inject summary recap drawing at start of drawConceptPanel body (after wantsHashMap/gc early returns)
    old_panel_start = '''  const footer = 48;
  const headerBottom = 360;
  const available = HEIGHT - footer - headerBottom;
  const panelH = Math.min(available, 520);
  const panelTop = headerBottom + Math.max(0, (available - panelH) / 2);
  const x = 28;
  const w = WIDTH - 108;
  const explainer =
    lesson?.reel_mode === "explainer" || Boolean(scene.diagram_steps && scene.diagram_steps.length);

  const t = elapsed;
'''
    new_panel_start = '''  const footer = 48;
  const headerBottom = 360;
  const available = HEIGHT - footer - headerBottom;
  const panelH = Math.min(available, 520);
  const panelTop = headerBottom + Math.max(0, (available - panelH) / 2);
  const x = 28;
  const w = WIDTH - 108;
  const explainer =
    lesson?.reel_mode === "explainer" || Boolean(scene.diagram_steps && scene.diagram_steps.length);

  // Summary end-card: animated checklist of every concept topic explained.
  if (lesson && scene.type === "summary") {
    const topics = lessonExplainedTopics(lesson);
    if (topics.length) {
      drawSummaryRecap(ctx, scene, elapsed, duration, topic, topics, panelTop, panelH, x, w);
      return;
    }
  }

  const t = elapsed;
'''
    must_replace(path, old_panel_start, new_panel_start, "summary recap branch in drawConceptPanel")

    # Append drawSummaryRecap before drawFrame
    marker = "\nfunction drawFrame(\n"
    helper = r'''
function drawSummaryRecap(
  ctx: CanvasRenderingContext2D,
  scene: LessonScene,
  elapsed: number,
  duration: number,
  topic: string,
  topics: string[],
  panelTop: number,
  panelH: number,
  x: number,
  w: number,
) {
  const t = elapsed;
  const orbs = [
    { cx: 90, cy: panelTop + 40, r: 70, color: "rgba(34,211,238,0.28)", drift: 1 },
    { cx: WIDTH - 130, cy: panelTop + 160, r: 58, color: "rgba(251,191,36,0.22)", drift: 1.4 },
    { cx: 140, cy: panelTop + panelH - 40, r: 48, color: "rgba(45,212,191,0.18)", drift: 0.8 },
  ];
  for (const orb of orbs) {
    const ox = Math.sin(t * orb.drift) * 10;
    const oy = Math.cos(t * orb.drift * 0.9) * 12;
    const g = ctx.createRadialGradient(orb.cx + ox, orb.cy + oy, 4, orb.cx + ox, orb.cy + oy, orb.r);
    g.addColorStop(0, orb.color);
    g.addColorStop(1, "transparent");
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.arc(orb.cx + ox, orb.cy + oy, orb.r, 0, Math.PI * 2);
    ctx.fill();
  }

  ctx.textAlign = "center";
  ctx.fillStyle = "rgba(103,232,249,0.95)";
  ctx.font = "700 16px ui-sans-serif, system-ui";
  ctx.fillText("WHAT WE COVERED", WIDTH / 2, 88);
  ctx.fillStyle = "#ffffff";
  ctx.font = "700 26px ui-sans-serif, system-ui";
  wrapLines(ctx, topic, WIDTH - 120, 2).forEach((line, index) => {
    ctx.fillText(line, WIDTH / 2, 122 + index * 30);
  });
  ctx.textAlign = "left";

  roundRect(ctx, x, panelTop, w, panelH, 22);
  ctx.fillStyle = "rgba(3,16,24,0.94)";
  ctx.fill();
  ctx.strokeStyle = "rgba(34,211,238,0.28)";
  ctx.lineWidth = 1.5;
  ctx.stroke();

  const anim = infoBulletAt(topics, elapsed, duration);
  const pad = 18;
  let y = panelTop + pad + 6;
  const rowH = Math.min(58, Math.max(42, (panelH - pad * 2 - 56) / Math.max(1, topics.length)));
  topics.forEach((item, index) => {
    const visible = index < anim.visibleCount;
    const active = index === anim.active && visible;
    if (!visible) return;
    const by = y + index * rowH;
    if (by + rowH > panelTop + panelH - 40) return;
    ctx.save();
    roundRect(ctx, x + pad, by, w - pad * 2, rowH - 8, 14);
    ctx.fillStyle = active ? "rgba(251,191,36,0.18)" : "rgba(0,0,0,0.4)";
    ctx.fill();
    ctx.strokeStyle = active ? "rgba(251,191,36,0.55)" : "rgba(255,255,255,0.1)";
    ctx.lineWidth = 1;
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(x + pad + 22, by + (rowH - 8) / 2, 11, 0, Math.PI * 2);
    ctx.fillStyle = active ? "#fbbf24" : "rgba(34,211,238,0.85)";
    ctx.fill();
    ctx.fillStyle = "#083344";
    ctx.font = "800 11px ui-sans-serif, system-ui";
    ctx.textAlign = "center";
    ctx.fillText("✓", x + pad + 22, by + (rowH - 8) / 2 + 4);
    ctx.textAlign = "left";
    ctx.fillStyle = active ? "#fef3c7" : "#f4f4f5";
    ctx.font = active ? "800 16px ui-sans-serif, system-ui" : "600 15px ui-sans-serif, system-ui";
    wrapLines(ctx, item, w - pad * 2 - 56, 2).forEach((line, li) => {
      ctx.fillText(line, x + pad + 42, by + 20 + li * 18);
    });
    ctx.restore();
  });

  const takeaways = (scene.takeaways || []).map((t) => String(t || "").trim()).filter(Boolean);
  const footerLine = takeaways.length
    ? takeaways.slice(0, 2).join(" · ")
    : "Follow for more · @techshalabypavi";
  ctx.fillStyle = "rgba(253,230,138,0.85)";
  ctx.font = "600 13px ui-sans-serif, system-ui";
  ctx.textAlign = "center";
  wrapLines(ctx, footerLine, w - 36, 2).forEach((line, index) => {
    ctx.fillText(line, x + w / 2, panelTop + panelH - 28 + index * 16);
  });
  ctx.textAlign = "left";
}

'''
    text = path.read_text(encoding="utf-8")
    if "function drawSummaryRecap(" in text:
        print("ok reelExport.ts :: drawSummaryRecap already present")
    elif marker not in text:
        raise SystemExit("MISSING drawFrame marker for drawSummaryRecap insert")
    else:
        path.write_text(text.replace(marker, helper + marker, 1), encoding="utf-8")
        print("ok frontend/lib/reelExport.ts :: drawSummaryRecap helper")


def main() -> None:
    patch_caption()
    patch_globals()
    patch_explainer_visuals()
    patch_reel_stage()
    patch_reel_export()
    print("ALL PATCHES APPLIED")


if __name__ == "__main__":
    main()
