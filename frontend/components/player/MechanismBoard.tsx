"use client";

import { useMemo } from "react";
import { cn } from "@/lib/utils";
import { cleanBoardTitle, dedupeBoardDetail } from "@/lib/explainerVisuals";

export type MechanismStep = { title: string; detail: string; example?: string };

export type MechanismBoardProps = {
  steps: MechanismStep[];
  active: number;
  progress: number;
  topic: string;
  phaseLabel?: string;
  phaseExample?: string;
};

export type GcPhase = "allocate" | "unref" | "mark" | "sweep" | "compact" | "other";

export function isGcTopic(topic: string): boolean {
  const t = (topic || "").toLowerCase();
  return /garbage|garbege|\bgc\b|heap|mark\s*[- ]?\s*sweep|marking|sweep|compact|collector|गारबेज|हिप|मार्क|स्वीप/.test(
    t,
  );
}

export function classifyGcPhase(title: string, detail?: string, example?: string): GcPhase {
  const blob = `${title || ""} ${detail || ""} ${example || ""}`.toLowerCase();
  if (/compact|defrag|relocat|पाक/.test(blob)) return "compact";
  if (/sweep|reclaim|collect|free|delete|remove|स्वीप|साफ/.test(blob)) return "sweep";
  if (/mark|reachable|root|live|मार्क|पहुंच/.test(blob)) return "mark";
  if (/unref|unreachable|dead|orphan|garbage|unused|बिना\s*संदर्भ|मृत/.test(blob)) return "unref";
  if (/allocat|new\b|create|object|heap|store|निर्माण|ऑब्जेक्ट|आवंटन/.test(blob)) return "allocate";
  return "other";
}

type HeapObj = {
  id: string;
  label: string;
  color: string;
  root: boolean;
};

const HEAP_OBJECTS: HeapObj[] = [
  { id: "A", label: "Obj A", color: "orange", root: true },
  { id: "B", label: "Obj B", color: "cyan", root: true },
  { id: "C", label: "Obj C", color: "violet", root: false },
  { id: "D", label: "Obj D", color: "emerald", root: false },
  { id: "E", label: "Obj E", color: "amber", root: false },
];

function clamp01(n: number) {
  return Math.max(0, Math.min(1, n));
}

function tone(color: string) {
  const map: Record<string, { border: string; bg: string; text: string; glow: string }> = {
    orange: {
      border: "border-orange-400/70",
      bg: "bg-orange-500/25",
      text: "text-orange-100",
      glow: "shadow-[0_0_18px_rgba(249,115,22,0.45)]",
    },
    cyan: {
      border: "border-cyan-400/70",
      bg: "bg-cyan-500/25",
      text: "text-cyan-100",
      glow: "shadow-[0_0_18px_rgba(34,211,238,0.45)]",
    },
    violet: {
      border: "border-violet-400/70",
      bg: "bg-violet-500/25",
      text: "text-violet-100",
      glow: "shadow-[0_0_18px_rgba(167,139,250,0.45)]",
    },
    emerald: {
      border: "border-emerald-400/70",
      bg: "bg-emerald-500/25",
      text: "text-emerald-100",
      glow: "shadow-[0_0_18px_rgba(16,185,129,0.45)]",
    },
    amber: {
      border: "border-amber-400/70",
      bg: "bg-amber-500/25",
      text: "text-amber-100",
      glow: "shadow-[0_0_18px_rgba(251,191,36,0.45)]",
    },
  };
  return map[color] || map.cyan;
}

/** Derive GC animation state from active step + local progress. */
function gcVisualState(phase: GcPhase, progress: number) {
  const p = clamp01(progress);
  // Objects: A,B roots; C linked from A; D unreferenced; E linked from B then becomes dead after unref
  const states: Record<
    string,
    { present: boolean; dim: boolean; marked: boolean; compacting: boolean }
  > = {
    A: { present: true, dim: false, marked: false, compacting: false },
    B: { present: true, dim: false, marked: false, compacting: false },
    C: { present: true, dim: false, marked: false, compacting: false },
    D: { present: true, dim: false, marked: false, compacting: false },
    E: { present: true, dim: false, marked: false, compacting: false },
  };

  if (phase === "allocate") {
    // Reveal objects gradually
    const count = 2 + Math.floor(p * 3.2); // 2..5
    ["A", "B", "C", "D", "E"].forEach((id, i) => {
      states[id].present = i < count;
    });
  } else if (phase === "unref") {
    states.D.dim = p > 0.25;
    states.E.dim = p > 0.55;
    states.C.dim = false;
  } else if (phase === "mark") {
    states.D.dim = true;
    states.E.dim = true;
    states.A.marked = p > 0.15;
    states.B.marked = p > 0.35;
    states.C.marked = p > 0.55; // reachable via A
  } else if (phase === "sweep") {
    states.A.marked = true;
    states.B.marked = true;
    states.C.marked = true;
    states.D.present = p < 0.45;
    states.D.dim = true;
    states.E.present = p < 0.7;
    states.E.dim = true;
  } else if (phase === "compact") {
    states.D.present = false;
    states.E.present = false;
    states.A.compacting = true;
    states.B.compacting = true;
    states.C.compacting = true;
    states.A.marked = p < 0.85;
    states.B.marked = p < 0.85;
    states.C.marked = p < 0.85;
  } else {
    // other / unknown — show full heap lightly
  }

  return states;
}

function GcHeapPanel({
  phase,
  progress,
  phaseLabel,
  phaseExample,
}: {
  phase: GcPhase;
  progress: number;
  phaseLabel?: string;
  phaseExample?: string;
}) {
  const states = useMemo(() => gcVisualState(phase, progress), [phase, progress]);
  const phaseTitle =
    phaseLabel ||
    ({
      allocate: "Allocate",
      unref: "Unreferenced",
      mark: "Mark reachable",
      sweep: "Sweep dead",
      compact: "Compact",
      other: "Heap",
    }[phase] as string);

  return (
    <div className="mechanism-gc relative flex min-h-0 flex-1 flex-col gap-2 overflow-hidden rounded-2xl border border-cyan-200/25 bg-[#031018]/94 p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]">
      <div className="mechanism-board-grid pointer-events-none absolute inset-0" aria-hidden />
      <div className="relative z-10 flex items-center justify-between gap-2">
        <span className="inline-flex rounded-full border border-amber-300/35 bg-amber-400/15 px-2.5 py-0.5 text-[10px] font-extrabold uppercase tracking-[0.18em] text-amber-100">
          GC · Heap
        </span>
        <span className="truncate text-[10px] font-semibold uppercase tracking-[0.14em] text-cyan-200/75">
          {phaseTitle}
        </span>
      </div>

      <div className="relative z-10 rounded-xl border border-white/10 bg-black/35 px-2.5 py-2">
        <p className="text-[9px] font-semibold uppercase tracking-[0.16em] text-zinc-500">Roots</p>
        <div className="mt-1 flex flex-wrap gap-1.5">
          {["A", "B"].map((id) => {
            const st = states[id];
            const obj = HEAP_OBJECTS.find((o) => o.id === id)!;
            const t = tone(obj.color);
            return (
              <span
                key={id}
                className={cn(
                  "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 font-mono text-[10px] font-bold",
                  st.marked ? cn(t.border, t.bg, t.glow, t.text) : "border-white/15 bg-white/5 text-zinc-300",
                )}
              >
                root → {obj.label}
              </span>
            );
          })}
        </div>
      </div>

      <div className="relative z-10 flex min-h-0 flex-1 flex-col">
        <p className="mb-1.5 text-[9px] font-semibold uppercase tracking-[0.16em] text-zinc-500">Heap</p>
        <div className="grid min-h-0 flex-1 grid-cols-3 gap-1.5 content-start">
          {HEAP_OBJECTS.map((obj, index) => {
            const st = states[obj.id];
            if (!st.present) {
              return (
                <div
                  key={obj.id}
                  className="flex h-[4.25rem] items-center justify-center rounded-xl border border-dashed border-white/10 bg-white/[0.02] font-mono text-[9px] text-zinc-600"
                >
                  free
                </div>
              );
            }
            const t = tone(obj.color);
            const slide = st.compacting ? clamp01(progress) : 1;
            return (
              <div
                key={obj.id}
                className={cn(
                  "mechanism-heap-obj relative flex h-[4.25rem] flex-col justify-between rounded-xl border px-2 py-1.5 transition-all duration-300",
                  t.border,
                  t.bg,
                  st.marked && t.glow,
                  st.dim && "opacity-35 grayscale",
                  st.marked && "mechanism-heap-marked",
                )}
                style={
                  st.compacting
                    ? {
                        transform: `translateX(${(1 - slide) * (index % 3 === 2 ? -10 : index % 3 === 0 ? 10 : 0)}px) scale(${0.94 + slide * 0.06})`,
                      }
                    : undefined
                }
              >
                <div className="flex items-center justify-between gap-1">
                  <span className={cn("font-mono text-[11px] font-extrabold", t.text)}>{obj.label}</span>
                  {st.marked ? (
                    <span className="rounded-full bg-lime-400/90 px-1.5 py-0.5 text-[8px] font-extrabold uppercase text-zinc-950">
                      mark
                    </span>
                  ) : st.dim ? (
                    <span className="rounded-full bg-zinc-500/40 px-1.5 py-0.5 text-[8px] font-bold uppercase text-zinc-300">
                      dead
                    </span>
                  ) : obj.root ? (
                    <span className="rounded-full bg-cyan-400/25 px-1.5 py-0.5 text-[8px] font-bold uppercase text-cyan-100">
                      live
                    </span>
                  ) : null}
                </div>
                <p className="font-mono text-[9px] leading-3 text-zinc-400">
                  {obj.root ? "← root" : obj.id === "C" ? "← A.next" : obj.id === "E" ? "orphan" : "no ref"}
                </p>
              </div>
            );
          })}
        </div>
      </div>

      {(phaseLabel || phaseExample) && (
        <div className="relative z-10 rounded-xl border border-cyan-300/25 bg-cyan-400/10 px-2.5 py-1.5">
          {phaseLabel ? <p className="truncate text-[11px] font-bold text-cyan-50">{phaseLabel}</p> : null}
          {phaseExample ? (
            <p className="mt-0.5 truncate font-mono text-[10px] text-amber-100/90">{phaseExample}</p>
          ) : null}
        </div>
      )}
    </div>
  );
}

function GenericStageBoard({
  steps,
  active,
  progress,
  topic,
  phaseLabel,
  phaseExample,
}: MechanismBoardProps) {
  const n = Math.max(1, steps.length);
  const safeActive = Math.max(0, Math.min(active, n - 1));
  const step = steps[safeActive] || { title: "", detail: "", example: "" };
  const example = String(phaseExample || step.example || "").trim();
  const title = cleanBoardTitle(String(phaseLabel || step.title || "").trim());
  const rawDetail = String(step.detail || "").trim();
  // Avoid stacking detail that repeats / prefixes the title (common when steps came from narration).
  const detail = dedupeBoardDetail(title, rawDetail);
  const tokenPct = n <= 1 ? 0 : (safeActive / (n - 1)) * 100;
  const p = clamp01(progress);

  return (
    <div className="mechanism-board relative flex min-h-0 flex-1 flex-col overflow-hidden rounded-2xl border border-cyan-200/25 bg-[#031018]/94 p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]">
      <div className="mechanism-board-grid pointer-events-none absolute inset-0" aria-hidden />

      <div className="relative z-10 flex min-h-0 flex-1 flex-col gap-3">
        <div className="mechanism-mini-pipeline relative mx-auto w-full max-w-[22rem] shrink-0 px-2 pt-1">
          <div
            className="pointer-events-none absolute left-4 right-4 top-1/2 h-[2px] -translate-y-1/2 rounded-full bg-cyan-400/15"
            aria-hidden
          />
          <div
            className="pointer-events-none absolute left-4 top-1/2 h-[2px] -translate-y-1/2 rounded-full bg-gradient-to-r from-cyan-400/70 via-amber-300/80 to-cyan-300/50 transition-[width] duration-500 ease-out"
            style={{ width: `calc((100% - 2rem) * ${tokenPct / 100})` }}
            aria-hidden
          />
          <ol className="relative z-10 flex items-center justify-between gap-1">
            {steps.map((s, index) => {
              const isActive = index === safeActive;
              const isPast = index < safeActive;
              return (
                <li
                  key={`mini-${index}-${s.title}`}
                  className={cn(
                    "flex h-8 w-8 items-center justify-center rounded-full border text-[10px] font-extrabold transition-all duration-300",
                    isActive &&
                      "border-amber-300/80 bg-amber-400/25 text-amber-100 shadow-[0_0_16px_rgba(251,191,36,0.45)]",
                    isPast && !isActive && "border-cyan-300/50 bg-cyan-400/30 text-cyan-50",
                    !isActive && !isPast && "border-white/10 bg-white/5 text-cyan-200/35 opacity-45",
                  )}
                  title={s.title}
                >
                  {index + 1}
                </li>
              );
            })}
          </ol>
        </div>

        <div className="relative flex min-h-0 flex-1 flex-col justify-center px-0.5 pb-0.5">
          <div
            key={`stage-${safeActive}-${title}`}
            className="mechanism-stage-card relative mx-auto flex w-full max-w-[22rem] flex-col gap-3 rounded-2xl border border-cyan-300/45 bg-[rgba(8,51,68,0.82)] px-3.5 py-3.5 shadow-[0_0_0_1px_rgba(34,211,238,0.28),0_16px_40px_rgba(8,145,178,0.35)] backdrop-blur-md"
            style={{ opacity: 0.55 + p * 0.45 }}
          >
            <span className="explainer-glow-ring pointer-events-none absolute inset-0 rounded-2xl" />
            <div className="relative z-10 flex items-center justify-between gap-2">
              <span className="inline-flex rounded-full border border-amber-300/35 bg-amber-400/15 px-2.5 py-0.5 text-[10px] font-extrabold uppercase tracking-[0.18em] text-amber-100">
                Stage {safeActive + 1} of {n}
              </span>
              <span className="text-[10px] font-semibold uppercase tracking-[0.16em] text-cyan-200/70">
                Mechanism
              </span>
            </div>

            <div className="relative z-10 min-w-0">
              <p className="text-[15px] font-extrabold leading-5 tracking-tight text-white">{title || topic}</p>
              {detail ? (
                <p className="mt-1.5 text-[12px] font-medium leading-4 text-cyan-100/90">{detail}</p>
              ) : null}
            </div>

            {example ? (
              <div
                key={`ex-${safeActive}-${example}`}
                className="explainer-example-chip relative z-10 rounded-xl border border-cyan-200/25 bg-black/45 px-3 py-2.5 font-mono text-[11.5px] font-semibold leading-4 tracking-tight text-amber-100 shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]"
              >
                <span className="mb-1 block text-[9px] font-bold uppercase tracking-[0.2em] text-cyan-300/70">
                  Example
                </span>
                <code className="block whitespace-pre-wrap break-words text-amber-50/95">{example}</code>
              </div>
            ) : null}
          </div>
        </div>
      </div>
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
  const gc = isGcTopic(topic);
  const safeActive = Math.max(0, Math.min(active, Math.max(0, steps.length - 1)));
  const step = steps[safeActive];
  const phase = useMemo(
    () => classifyGcPhase(step?.title || "", step?.detail, step?.example),
    [step?.title, step?.detail, step?.example],
  );

  // Prefer step-driven phase labels when parent didn't pass them
  const label = phaseLabel || step?.title || "";
  const example = phaseExample || step?.example || step?.detail || "";

  if (gc) {
    return (
      <div className="flex min-h-0 flex-1 flex-col gap-2">
        <GcHeapPanel phase={phase} progress={progress} phaseLabel={label} phaseExample={example} />
        {/* Tiny stage strip so GC still shows mechanism steps */}
        {steps.length > 1 ? (
          <div className="relative z-10 flex shrink-0 gap-1 overflow-x-auto px-0.5 pb-0.5">
            {steps.map((s, index) => (
              <span
                key={`chip-${index}-${s.title}`}
                className={cn(
                  "whitespace-nowrap rounded-full border px-2 py-0.5 text-[9px] font-bold uppercase tracking-wide",
                  index === safeActive
                    ? "border-amber-300/50 bg-amber-400/20 text-amber-100"
                    : index < safeActive
                      ? "border-cyan-300/30 bg-cyan-400/15 text-cyan-100/80"
                      : "border-white/10 bg-white/5 text-zinc-500",
                )}
              >
                {index + 1}. {s.title.slice(0, 18)}
              </span>
            ))}
          </div>
        ) : null}
      </div>
    );
  }

  return (
    <GenericStageBoard
      steps={steps}
      active={active}
      progress={progress}
      topic={topic}
      phaseLabel={label}
      phaseExample={example}
    />
  );
}
