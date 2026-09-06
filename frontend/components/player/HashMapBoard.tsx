"use client";

import { useMemo } from "react";
import { cn } from "@/lib/utils";
import type { PhaseKind } from "@/lib/hashmapPhase";
import type { HashMapPutStep, HashMapVisual } from "@/types/lesson";

export type HashMapBoardProps = {
  visual: HashMapVisual;
  activePutIndex: number;
  progress: number;
  topic: string;
  phaseLabel?: string;
  phaseExample?: string;
  phaseKind?: PhaseKind;
};

const COLOR_MAP: Record<string, { chip: string; border: string; glow: string; text: string }> = {
  orange: {
    chip: "bg-orange-500/90 text-zinc-950 border-orange-300/50",
    border: "border-orange-400/70",
    glow: "shadow-[0_0_18px_rgba(249,115,22,0.35)]",
    text: "text-orange-100",
  },
  blue: {
    chip: "bg-sky-500/90 text-zinc-950 border-sky-300/50",
    border: "border-sky-400/70",
    glow: "shadow-[0_0_18px_rgba(14,165,233,0.35)]",
    text: "text-sky-100",
  },
  green: {
    chip: "bg-emerald-500/90 text-zinc-950 border-emerald-300/50",
    border: "border-emerald-400/70",
    glow: "shadow-[0_0_18px_rgba(16,185,129,0.35)]",
    text: "text-emerald-100",
  },
  amber: {
    chip: "bg-amber-400/95 text-zinc-950 border-amber-200/50",
    border: "border-amber-300/70",
    glow: "shadow-[0_0_18px_rgba(251,191,36,0.35)]",
    text: "text-amber-100",
  },
  cyan: {
    chip: "bg-cyan-400/95 text-zinc-950 border-cyan-200/50",
    border: "border-cyan-300/70",
    glow: "shadow-[0_0_18px_rgba(34,211,238,0.35)]",
    text: "text-cyan-100",
  },
};

function tone(color?: string) {
  return COLOR_MAP[(color || "orange").toLowerCase()] || COLOR_MAP.orange;
}

function clamp01(n: number) {
  return Math.max(0, Math.min(1, n));
}

function isCollision(puts: HashMapPutStep[], index: number): boolean {
  if (index <= 0) return false;
  const bucket = puts[index]?.bucket;
  return puts.slice(0, index).some((p) => p.bucket === bucket);
}

export function HashMapBoard({
  visual,
  activePutIndex,
  progress,
  topic,
  phaseLabel,
  phaseExample,
  phaseKind,
}: HashMapBoardProps) {
  const capacity = Math.max(4, Math.min(32, visual.capacity ?? 8));
  const puts = visual.puts || [];
  const fields = visual.node_fields?.length ? visual.node_fields : ["key", "value", "hash", "next"];
  const p = clamp01(progress);
  const safeActive = Math.min(activePutIndex, puts.length - 1);
  const placedThrough = safeActive < 0 ? -1 : safeActive;

  const buckets = useMemo(() => {
    const map = new Map<number, { put: HashMapPutStep; index: number }[]>();
    for (let i = 0; i <= placedThrough; i++) {
      const put = puts[i];
      if (!put) continue;
      // While current put is sliding in (early progress), wait to attach until ~0.35
      if (i === safeActive && p < 0.08) continue;
      const list = map.get(put.bucket) || [];
      list.push({ put, index: i });
      map.set(put.bucket, list);
    }
    return map;
  }, [puts, placedThrough, safeActive, p]);

  const activePut = safeActive >= 0 ? puts[safeActive] : null;
  // During hash/index phases keep formula+first put preview so the board is never blank.
  const previewPut = !activePut && (phaseKind === "hash" || phaseKind === "index" || phaseKind === "other") ? puts[0] || null : null;
  const focusPut = activePut || previewPut;
  const colliding = activePut ? isCollision(puts, safeActive) : false;
  const showEquals = Boolean(activePut && colliding && p >= 0.2 && p < 0.85);
  const formulaBucket = focusPut?.bucket;
  const showPhase = Boolean(phaseLabel || phaseExample);

  return (
    <div className="hashmap-board relative flex min-h-0 flex-1 flex-col overflow-hidden rounded-2xl border border-cyan-200/20 bg-[#0b1220]/96 p-2.5 shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]">
      <div className="hashmap-board-grid pointer-events-none absolute inset-0" aria-hidden />

      {/* Top: code + puts + formula + phase */}
      <div className="relative z-10 flex shrink-0 flex-col gap-1.5">
        <div className="hashmap-init-chip truncate rounded-lg border border-emerald-400/35 bg-emerald-500/15 px-2.5 py-1.5 font-mono text-[11px] font-semibold leading-4 text-emerald-100">
          {visual.init_code || "Map<K,V> map = new HashMap<>();"}
        </div>
        {(visual.setup_lines || []).length ? (
          <div className="flex flex-col gap-0.5 px-0.5">
            {(visual.setup_lines || []).slice(0, 3).map((line) => (
              <p key={line} className="truncate font-mono text-[10px] leading-3.5 text-zinc-400">
                {line}
              </p>
            ))}
          </div>
        ) : null}

        <div className="flex flex-wrap gap-1">
          {puts.map((put, index) => {
            const t = tone(put.color);
            const active = index === safeActive || (safeActive < 0 && previewPut && index === 0);
            const past = index < safeActive;
            return (
              <span
                key={`${put.code}-${index}`}
                className={cn(
                  "hashmap-put-pill inline-flex max-w-full truncate rounded-full border px-2 py-0.5 font-mono text-[10px] font-bold transition-all duration-300",
                  active ? cn(t.chip, t.glow, "scale-105") : past ? cn(t.chip, "opacity-70") : "border-white/10 bg-white/5 text-zinc-500",
                )}
              >
                {put.code || `put(${put.key})`}
              </span>
            );
          })}
        </div>

        <div className="hashmap-formula rounded-xl border border-white/10 bg-black/40 px-2.5 py-1.5">
          <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-zinc-400">put(K,V) → hash(k) → index</p>
          <div className="mt-1 flex items-center gap-1.5">
            <span className="font-mono text-[11px] text-zinc-200">hash & (n-1)</span>
            {formulaBucket != null ? (
              <span
                className={cn(
                  "inline-flex h-6 min-w-6 items-center justify-center rounded-full border text-[11px] font-extrabold",
                  colliding && showEquals
                    ? "border-lime-300/70 bg-lime-400 text-zinc-950 shadow-[0_0_14px_rgba(163,230,53,0.55)]"
                    : "border-cyan-300/50 bg-cyan-400/90 text-zinc-950",
                )}
              >
                {formulaBucket}
              </span>
            ) : (
              <span className="inline-flex h-6 min-w-6 items-center justify-center rounded-full border border-white/15 bg-white/5 text-[10px] text-zinc-500">
                ?
              </span>
            )}
            {focusPut?.hash_bits ? (
              <span className="truncate font-mono text-[10px] text-zinc-500">{focusPut.hash_bits}</span>
            ) : null}
          </div>
          {showEquals ? (
            <p className="hashmap-equals mt-1 text-[10px] font-bold uppercase tracking-wide text-lime-300">
              equals? same bucket → chain via next
            </p>
          ) : null}
          {showPhase ? (
            <div
              className={cn(
                "mt-1.5 rounded-lg border px-2 py-1",
                phaseKind === "collision"
                  ? "border-lime-300/35 bg-lime-400/10"
                  : phaseKind === "tree"
                    ? "border-violet-300/35 bg-violet-400/10"
                    : "border-cyan-300/25 bg-cyan-400/10",
              )}
            >
              {phaseLabel ? (
                <p className="truncate text-[10px] font-bold leading-4 text-cyan-50">{phaseLabel}</p>
              ) : null}
              {phaseExample ? (
                <p className="mt-0.5 truncate font-mono text-[9px] leading-3.5 text-zinc-300">{phaseExample}</p>
              ) : null}
            </div>
          ) : null}
        </div>

        <div className="flex items-center gap-1.5 px-0.5">
          <span className="text-[9px] font-semibold uppercase tracking-[0.16em] text-zinc-500">Node</span>
          {fields.map((f) => (
            <span
              key={f}
              className="rounded border border-white/10 bg-white/5 px-1.5 py-0.5 font-mono text-[9px] font-semibold uppercase tracking-wide text-zinc-300"
            >
              {f}
            </span>
          ))}
        </div>
      </div>

      {/* Bottom: one flex row per bucket [index cell][chain of nodes] */}
      <div className="relative z-10 mt-2 flex min-h-0 flex-1 flex-col gap-0.5 overflow-y-auto pb-1">
        {Array.from({ length: capacity }).map((_, bucket) => {
          const chain = buckets.get(bucket) || [];
          const filled = chain.length > 0;
          const active = (activePut?.bucket === bucket || (safeActive < 0 && previewPut?.bucket === bucket)) && p >= 0.15;
          return (
            <div key={bucket} className="flex min-h-[26px] items-stretch gap-1.5">
              <div
                className={cn(
                  "hashmap-bucket flex w-[2.75rem] shrink-0 items-center justify-center rounded-md border font-mono text-[10px] font-bold transition-all duration-300",
                  active
                    ? "border-cyan-300/70 bg-cyan-400/25 text-cyan-50 shadow-[0_0_12px_rgba(34,211,238,0.35)]"
                    : filled
                      ? "border-sky-300/35 bg-sky-400/15 text-sky-100"
                      : "border-sky-400/20 bg-sky-500/10 text-sky-200/80",
                )}
              >
                {bucket}
              </div>

              <div className="flex min-w-0 flex-1 flex-row flex-wrap items-center gap-1">
                {chain.map(({ put, index }, chainIdx) => {
                  const t = tone(put.color);
                  const isNew = index === safeActive;
                  const slide = isNew ? clamp01((p - 0.35) / 0.45) : 1;
                  const nextExists = chainIdx < chain.length - 1;
                  return (
                    <div key={`${put.key}-${index}`} className="flex flex-row items-center gap-1">
                      <div
                        className={cn(
                          "hashmap-node rounded-xl border bg-black/55 px-2 py-1 backdrop-blur-sm",
                          t.border,
                          isNew && t.glow,
                          isNew && "hashmap-node-enter",
                        )}
                        style={
                          isNew
                            ? {
                                opacity: 0.35 + slide * 0.65,
                                transform: `translateX(${(1 - slide) * 28}px) translateY(${(1 - slide) * -8}px) scale(${0.92 + slide * 0.08})`,
                              }
                            : undefined
                        }
                      >
                        <div className="flex items-center justify-between gap-2">
                          <span className={cn("font-mono text-[11px] font-extrabold", t.text)}>{put.key}</span>
                          <span className="rounded-full bg-white/10 px-1.5 py-0.5 font-mono text-[9px] text-zinc-300">
                            #{put.bucket}
                          </span>
                        </div>
                        <div className="mt-0.5 grid grid-cols-2 gap-x-2 gap-y-0.5">
                          <span className="font-mono text-[9px] text-zinc-500">value</span>
                          <span className="truncate font-mono text-[10px] font-semibold text-zinc-100">{put.value}</span>
                          <span className="font-mono text-[9px] text-zinc-500">hash</span>
                          <span className="truncate font-mono text-[10px] text-zinc-300">{put.hash_bits || "—"}</span>
                          <span className="font-mono text-[9px] text-zinc-500">next</span>
                          <span className={cn("font-mono text-[10px] font-bold", nextExists ? "text-lime-300" : "text-zinc-500")}>
                            {nextExists ? chain[chainIdx + 1].put.key : "null"}
                          </span>
                        </div>
                      </div>
                      {nextExists ? (
                        <div className="hashmap-next-arrow flex shrink-0 items-center gap-0.5 px-0.5">
                          <span className="h-0.5 w-3 rounded-full bg-lime-400 shadow-[0_0_8px_rgba(163,230,53,0.8)]" />
                          <span className="text-[8px] font-extrabold uppercase tracking-wide text-lime-300">next</span>
                        </div>
                      ) : null}
                    </div>
                  );
                })}
                {!filled && active ? (
                  <span className="font-mono text-[9px] text-cyan-300/70">← landing…</span>
                ) : null}
              </div>
            </div>
          );
        })}
        {placedThrough < 0 ? (
          <p className="mt-4 text-center text-[11px] font-medium text-zinc-500">
            Empty table · capacity {capacity}
            <span className="mt-1 block text-[10px] text-zinc-600">{topic}</span>
          </p>
        ) : null}
      </div>
    </div>
  );
}
