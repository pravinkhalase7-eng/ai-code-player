"use client";

import { useMemo } from "react";
import {
  AppWindow,
  Binary,
  Box,
  Braces,
  Cpu,
  Database,
  Factory,
  FileCode,
  Hash,
  Hexagon,
  Key,
  Layers,
  MemoryStick,
  Package,
  PhoneCall,
  SquareFunction,
  Workflow,
  Zap,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";

export type ExplainerFlowStep = { title: string; detail: string; example?: string };

export type ExplainerFlowProps = {
  steps: ExplainerFlowStep[];
  active: number;
  visibleCount: number;
  topic: string;
};

function pickIcon(title: string, detail: string, topic: string): LucideIcon {
  const t = `${title} ${detail} ${topic}`.toLowerCase();
  if (/\b(interface|ui|window|panel|screen)\b/.test(t)) return AppWindow;
  if (/\b(lambda|function|fn\b|closure)\b/.test(t)) return SquareFunction;
  if (/\b(bytecode|binary|byte|opcode|asm)\b/.test(t)) return Binary;
  if (/\b(factory|builder|create|construct|निर्माण|new)\b/.test(t)) return Factory;
  if (/\b(call|invoke|dispatch|phone)\b/.test(t)) return PhoneCall;
  if (/\b(hash|digest|checksum)\b/.test(t)) return Hash;
  if (/\b(bucket|map|dict|table|store|db|database)\b/.test(t)) return Database;
  if (/\b(key|lookup|index)\b/.test(t)) return Key;
  if (/\b(value|payload|data|object|ऑब्जेक्ट)\b/.test(t)) return Box;
  if (/\b(memory|heap|stack|ram|cache|sweep|मार्किंग|स्वीप|मेमोरी|हिप)\b/.test(t)) return MemoryStick;
  if (/\b(package|module|import)\b/.test(t)) return Package;
  if (/\b(cpu|runtime|vm|process|gc|गारबेज)\b/.test(t)) return Cpu;
  if (/\b(layer|pipeline|stage)\b/.test(t)) return Layers;
  if (/\b(flow|pipeline|workflow|graph)\b/.test(t)) return Workflow;
  if (/\b(code|source|script)\b/.test(t)) return FileCode;
  if (/\b(brace|syntax|parse)\b/.test(t)) return Braces;
  if (/\b(spark|fast|power|energy)\b/.test(t)) return Zap;
  return Hexagon;
}

export function ExplainerFlow({ steps, active, visibleCount, topic }: ExplainerFlowProps) {
  const n = Math.max(1, steps.length);
  const safeActive = Math.max(0, Math.min(active, n - 1));
  const tokenPct = n <= 1 ? 0 : (safeActive / (n - 1)) * 100;
  const step = steps[safeActive] || { title: "", detail: "", example: "" };
  const example = String(step.example || "").trim();

  const icons = useMemo(
    () => steps.map((s) => pickIcon(s.title, s.detail, topic)),
    [steps, topic],
  );
  const ActiveIcon = icons[safeActive] || Hexagon;

  return (
    <div className="explainer-flow relative flex min-h-0 flex-1 flex-col overflow-hidden rounded-2xl border border-cyan-200/25 bg-[#031018]/94 p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]">
      <div className="explainer-flow-grid pointer-events-none absolute inset-0" aria-hidden />

      <div className="relative z-10 flex min-h-0 flex-1 flex-col gap-5">
        {/* Mini pipeline */}
        <div className="explainer-mini-pipeline relative mx-auto w-full max-w-[22rem] shrink-0 px-3 pt-2 pb-1">
          <div className="pointer-events-none absolute left-5 right-5 top-1/2 z-0 h-[2px] -translate-y-1/2 rounded-full bg-cyan-400/20" aria-hidden />
          <div
            className="pointer-events-none absolute left-5 top-1/2 z-0 h-[2px] -translate-y-1/2 rounded-full bg-gradient-to-r from-cyan-400/80 via-amber-300/85 to-cyan-300/55 transition-[width] duration-500 ease-out"
            style={{ width: `calc((100% - 2.5rem) * ${tokenPct / 100})` }}
            aria-hidden
          />
          <div
            className="explainer-token pointer-events-none absolute top-1/2 z-20 transition-[left] duration-500 ease-out"
            style={{ left: `calc(1.25rem + (100% - 2.5rem) * ${tokenPct / 100})`, transform: "translate(-50%, -50%)" }}
            aria-hidden
          >
            <span className="explainer-token-orb" />
          </div>
          <ol className="relative z-10 flex items-center justify-between gap-2">
            {steps.map((s, index) => {
              const Icon = icons[index] || Hexagon;
              const visible = visibleCount > index;
              const isActive = active === index && visible;
              const isPast = visible && index < active;
              const isFuture = !visible || index > active;
              return (
                <li
                  key={`mini-${index}-${s.title}`}
                  className={cn(
                    "explainer-mini-node relative z-10 flex h-9 w-9 items-center justify-center rounded-full border-2 transition-all duration-300 ring-4 ring-[#031018]",
                    isActive && "is-active border-amber-300 bg-[#3b2a0a] text-amber-100 shadow-[0_0_18px_rgba(251,191,36,0.5)]",
                    isPast && !isActive && "border-cyan-300 bg-[#0a3a45] text-cyan-50",
                    isFuture && !isActive && "border-white/20 bg-[#0a1c24] text-cyan-200/55",
                  )}
                  title={s.title}
                >
                  <Icon className={cn("h-3.5 w-3.5", isActive && "animate-pulse")} strokeWidth={2.4} />
                </li>
              );
            })}
          </ol>
        </div>

        {/* ONE large active stage card */}
        <div className="relative flex min-h-0 flex-1 flex-col justify-center px-0.5 pb-0.5">
          <div
            key={`stage-${safeActive}-${step.title}`}
            className="explainer-stage-card relative mx-auto flex w-full max-w-[22rem] flex-col gap-3 rounded-2xl border border-cyan-300/45 bg-[rgba(8,51,68,0.82)] px-4 py-4 shadow-[0_0_0_1px_rgba(34,211,238,0.28),0_16px_40px_rgba(8,145,178,0.35)] backdrop-blur-md"
          >
            <span className="explainer-glow-ring pointer-events-none absolute inset-0 rounded-2xl" />
            <div className="relative z-10 flex items-center justify-between gap-2">
              <span className="inline-flex rounded-full border border-amber-300/35 bg-amber-400/15 px-2.5 py-0.5 text-[10px] font-extrabold uppercase tracking-[0.18em] text-amber-100">
                Step {safeActive + 1} of {n}
              </span>
              <span className="text-[10px] font-semibold uppercase tracking-[0.16em] text-cyan-200/70">
                Mechanism
              </span>
            </div>

            <div className="relative z-10 flex items-start gap-3">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-cyan-300/45 bg-cyan-400/20 text-cyan-50 shadow-[0_0_18px_rgba(34,211,238,0.35)]">
                <ActiveIcon className="h-5 w-5" strokeWidth={2.25} />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-[15px] font-extrabold leading-5 tracking-tight text-white">{step.title}</p>
                {step.detail ? (
                  <p className="mt-1.5 text-[12px] font-medium leading-4 text-cyan-100/90">{step.detail}</p>
                ) : null}
              </div>
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
