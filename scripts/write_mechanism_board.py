from pathlib import Path

board = Path("frontend/components/player/MechanismBoard.tsx")
board.write_text(r'''"use client";

import { cn } from "@/lib/utils";

export type MechanismStep = { title: string; detail?: string; example?: string };

export type MechanismBoardProps = {
  steps: MechanismStep[];
  active: number;
  progress: number;
  topic: string;
  phaseLabel?: string;
  phaseExample?: string;
};

function isGcTopic(topic: string) {
  return /\b(garbage|gc\b|heap|mark|sweep|compact|collector)\b/i.test(topic || "");
}

function clamp01(n: number) {
  return Math.max(0, Math.min(1, n));
}

/** Simple heap objects that animate through GC phases. */
function GcHeapVisual({ active, progress, stepCount }: { active: number; progress: number; stepCount: number }) {
  const p = clamp01(progress);
  const phase = Math.max(0, Math.min(active, Math.max(0, stepCount - 1)));
  // 0 allocate, 1 unreferenced, 2 mark, 3 sweep, 4 compact
  const objects = [
    { id: "A", live: true },
    { id: "B", live: true },
    { id: "C", live: false },
    { id: "D", live: true },
    { id: "E", live: false },
  ];

  return (
    <div className="mechanism-heap relative mt-2 flex min-h-0 flex-1 flex-col rounded-xl border border-amber-300/20 bg-black/35 p-2">
      <p className="mb-1 text-[9px] font-bold uppercase tracking-[0.16em] text-amber-200/80">Heap</p>
      <div className="flex flex-wrap content-start gap-1.5">
        {objects.map((obj, index) => {
          const allocated = phase >= 0;
          const unreferenced = phase >= 1 && !obj.live;
          const marked = phase >= 2 && obj.live;
          const swept = phase >= 3 && !obj.live;
          const compacted = phase >= 4 && obj.live;
          if (swept) return null;
          return (
            <div
              key={obj.id}
              className={cn(
                "flex h-10 w-10 flex-col items-center justify-center rounded-lg border font-mono text-[11px] font-extrabold transition-all duration-500",
                !allocated && "opacity-0 scale-75",
                allocated && !unreferenced && !marked && "border-sky-300/40 bg-sky-500/20 text-sky-100",
                unreferenced && !swept && "border-zinc-500/50 bg-zinc-700/40 text-zinc-400 opacity-50",
                marked && "border-lime-300/70 bg-lime-400/25 text-lime-100 shadow-[0_0_14px_rgba(163,230,53,0.45)]",
                compacted && "translate-y-0",
              )}
              style={{
                transitionDelay: `${index * 40}ms`,
                opacity: allocated ? (unreferenced && phase === 1 ? 0.45 + p * 0.2 : 1) : 0,
                transform: compacted ? `translateX(${(index % 3) * -2}px)` : undefined,
              }}
            >
              {obj.id}
              <span className="text-[8px] font-semibold opacity-70">{obj.live ? "live" : "dead"}</span>
            </div>
          );
        })}
      </div>
      <p className="mt-auto pt-2 text-[9px] font-medium text-zinc-500">
        {phase <= 0 && "new → objects land in heap"}
        {phase === 1 && "refs cleared → unreachable"}
        {phase === 2 && "GC marks reachable graph"}
        {phase === 3 && "sweep frees unmarked"}
        {phase >= 4 && "compact reduces free space"}
      </p>
    </div>
  );
}

export function MechanismBoard({
  steps,
  active,
  progress,
  topic,
  phaseLabel,
  phaseExample,
}: MechanismBoardProps) {
  const n = Math.max(1, steps.length);
  const safeActive = Math.max(0, Math.min(active, n - 1));
  const step = steps[safeActive] || { title: topic, detail: "", example: "" };
  const gc = isGcTopic(topic) || steps.some((s) => /\b(mark|sweep|compact|heap|garbage)\b/i.test(s.title));
  const label = phaseLabel || step.title;
  const example = phaseExample || step.example || "";

  return (
    <div className="mechanism-board relative flex min-h-0 flex-1 flex-col overflow-hidden rounded-2xl border border-cyan-200/20 bg-[#0b1220]/96 p-2.5 shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]">
      <div className="pointer-events-none absolute inset-0 opacity-40" style={{ backgroundImage: "radial-gradient(circle at 20% 20%, rgba(34,211,238,0.12), transparent 40%), radial-gradient(circle at 80% 70%, rgba(251,191,36,0.1), transparent 35%)" }} />

      <div className="relative z-10 flex shrink-0 gap-1 overflow-x-auto pb-1">
        {steps.map((item, index) => {
          const on = index === safeActive;
          const past = index < safeActive;
          return (
            <span
              key={`${index}-${item.title}`}
              className={cn(
                "inline-flex shrink-0 items-center gap-1 rounded-full border px-2 py-0.5 text-[9px] font-bold transition-all",
                on && "border-amber-300/60 bg-amber-400 text-zinc-950",
                past && !on && "border-cyan-300/30 bg-cyan-400/15 text-cyan-100",
                !on && !past && "border-white/10 bg-white/5 text-zinc-500",
              )}
            >
              <span className="opacity-70">{index + 1}</span>
              {item.title.replace(/^\d+\.\s*/, "").slice(0, 18)}
            </span>
          );
        })}
      </div>

      <div className="relative z-10 mt-1 rounded-xl border border-white/10 bg-black/45 px-3 py-2">
        <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-zinc-500">Stage</p>
        <p className="mt-0.5 text-sm font-extrabold leading-5 text-white">{label}</p>
        {step.detail ? <p className="mt-1 text-[11px] leading-4 text-cyan-100/80">{step.detail}</p> : null}
        {example ? (
          <p className="mt-1.5 rounded-lg border border-cyan-300/20 bg-cyan-400/10 px-2 py-1 font-mono text-[10px] font-semibold text-cyan-50">
            {example}
          </p>
        ) : null}
      </div>

      {gc ? <GcHeapVisual active={safeActive} progress={progress} stepCount={n} /> : (
        <div className="relative z-10 mt-2 flex min-h-0 flex-1 flex-col justify-center gap-1.5">
          {steps.map((item, index) => {
            const on = index === safeActive;
            const visible = index <= safeActive;
            return (
              <div
                key={`row-${index}`}
                className={cn(
                  "rounded-xl border px-2.5 py-1.5 transition-all duration-300",
                  !visible && "opacity-20",
                  visible && !on && "border-white/10 bg-black/30 opacity-70",
                  on && "border-cyan-300/50 bg-cyan-400/15 shadow-[0_0_16px_rgba(34,211,238,0.25)]",
                )}
              >
                <p className="text-[11px] font-bold text-zinc-100">{item.title}</p>
                {on && item.detail ? <p className="text-[10px] text-cyan-100/75">{item.detail}</p> : null}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
''')
print("wrote", board)

# Wire ReelStage
stage = Path("frontend/components/player/ReelStage.tsx")
text = stage.read_text()
if "MechanismBoard" not in text:
    text = text.replace(
        'import { HashMapBoard } from "@/components/player/HashMapBoard";',
        'import { HashMapBoard } from "@/components/player/HashMapBoard";\nimport { MechanismBoard } from "@/components/player/MechanismBoard";',
    )
    old = """            {isExplainer && hashmapVisual ? (
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
              <ExplainerFlow
                steps={diagramSteps}
                active={infoAnim?.active ?? 0}
                visibleCount={infoAnim?.visibleCount ?? 0}
                topic={topic}
              />
            ) : ("""
    new = """            {isExplainer && hashmapVisual ? (
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
            ) : ("""
    if old not in text:
        # try without phaseKind line variations
        raise SystemExit("ReelStage HashMap/ExplainerFlow block not found")
    text = text.replace(old, new, 1)
    # Also use segment beats for any explainer with diagram steps, not only hashmap
    old_anim = """    if (hashmapVisual && segs.length >= 2) {
      const beats = beatsFromSegments(segs, duration);
      return infoBulletAtBeats(beats, currentTime);
    }"""
    new_anim = """    if ((hashmapVisual || diagramSteps.length) && segs.length >= 2) {
      const beats = beatsFromSegments(segs, duration);
      return infoBulletAtBeats(beats, currentTime);
    }"""
    if old_anim in text:
        text = text.replace(old_anim, new_anim, 1)
    # boardState for non-hashmap too when diagram steps exist
    old_bs = """  const boardState = useMemo(() => {
    if (!hashmapVisual || !diagramSteps.length) return null;
    return boardStateFromSteps(diagramSteps, infoAnim?.active ?? 0, hashmapVisual.puts?.length ?? 0);
  }, [hashmapVisual, diagramSteps, infoAnim?.active]);"""
    new_bs = """  const boardState = useMemo(() => {
    if (!diagramSteps.length) return null;
    const putCount = hashmapVisual?.puts?.length ?? 0;
    return boardStateFromSteps(diagramSteps, infoAnim?.active ?? 0, putCount);
  }, [hashmapVisual, diagramSteps, infoAnim?.active]);"""
    if old_bs in text:
        text = text.replace(old_bs, new_bs, 1)
    stage.write_text(text)
    print("ReelStage wired")
else:
    print("MechanismBoard already referenced")

print("done")
