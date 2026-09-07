#!/usr/bin/env python3
"""Add HashMapVisual schema, HashMapBoard UI, planner/orchestrator synthesis, export+CSS."""
from __future__ import annotations

from pathlib import Path

ROOT = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder")


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        if new.strip()[:80] in text or label.split(":")[0] in ("SKIP",):
            print(f"SKIP {path.name}: {label}")
            return
        # idempotent check
        marker = new.strip().split("\n")[0][:60]
        if marker and marker in text and old.strip()[:40] not in text:
            print(f"SKIP {path.name}: {label} (already applied)")
            return
        raise SystemExit(f"MISSING in {path}: {label}\n---\n{old[:240]}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"OK {path.relative_to(ROOT)}: {label}")


def patch_schema() -> None:
    path = ROOT / "backend/app/schemas/lesson.py"
    text = path.read_text(encoding="utf-8")
    if "class HashMapVisual" in text:
        print("SKIP lesson.py: HashMapVisual already present")
    else:
        old = '''class DiagramStep(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    detail: str = Field(default="", max_length=240)
    example: str = Field(default="", max_length=160)


class ConceptScene(BaseScene):
    type: Literal["concept"] = "concept"
    concept_id: str = "for_loop"
    bullets: list[str] = Field(default_factory=list, max_length=8)
    diagram_steps: list[DiagramStep] = Field(default_factory=list, max_length=8)
'''
        new = '''class DiagramStep(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    detail: str = Field(default="", max_length=240)
    example: str = Field(default="", max_length=160)


class HashMapPutStep(BaseModel):
    code: str = Field(max_length=120)
    key: str = Field(max_length=40)
    value: str = Field(max_length=40)
    hash_bits: str = Field(default="", max_length=32)
    bucket: int = Field(ge=0, le=63)
    color: str = Field(default="orange", max_length=32)


class HashMapVisual(BaseModel):
    kind: Literal["hashmap"] = "hashmap"
    capacity: int = Field(default=8, ge=4, le=32)
    init_code: str = Field(default="Map<K,V> map = new HashMap<>();", max_length=160)
    setup_lines: list[str] = Field(default_factory=list, max_length=8)
    puts: list[HashMapPutStep] = Field(default_factory=list, max_length=8)
    node_fields: list[str] = Field(default_factory=lambda: ["key", "value", "hash", "next"])


class ConceptScene(BaseScene):
    type: Literal["concept"] = "concept"
    concept_id: str = "for_loop"
    bullets: list[str] = Field(default_factory=list, max_length=8)
    diagram_steps: list[DiagramStep] = Field(default_factory=list, max_length=8)
    visual_diagram: HashMapVisual | None = None
'''
        replace_once(path, old, new, "HashMapVisual + ConceptScene.visual_diagram")

    text = path.read_text(encoding="utf-8")
    if "visual_diagram" not in text[text.index("class GenericScene") : text.index("class LessonDraft")]:
        old_g = '''    concept_id: str = "for_loop"
    diagram_steps: list[DiagramStep] = Field(default_factory=list, max_length=8)


class LessonDraft'''
        new_g = '''    concept_id: str = "for_loop"
    diagram_steps: list[DiagramStep] = Field(default_factory=list, max_length=8)
    visual_diagram: HashMapVisual | None = None


class LessonDraft'''
        replace_once(path, old_g, new_g, "GenericScene.visual_diagram")
    else:
        print("SKIP lesson.py: GenericScene.visual_diagram already present")


def patch_frontend_types() -> None:
    path = ROOT / "frontend/types/lesson.ts"
    text = path.read_text(encoding="utf-8")
    if "HashMapVisual" in text:
        print("SKIP lesson.ts: HashMapVisual already present")
        return
    old = '''export type LessonScene = {
  id: string;
  type: SceneType;
  duration: number;
  narration: string;
  segments?: NarrationSegment[];
  expression?: TutorExpression;
  audio_url?: string | null;
  language?: string;
  filename?: string;
  code?: string;
  highlight_ranges?: HighlightRange[];
  expected_output?: string[];
  iterations?: ExecutionStep[];
  command?: string;
  stdout?: string[];
  stderr?: string;
  success?: boolean;
  verified?: boolean;
  kind?: string;
  question?: string;
  options?: string[];
  answer?: number | string | null;
  explanation?: string;
  bullets?: string[];
  diagram_steps?: { title: string; detail?: string; example?: string }[];
  takeaways?: string[];
  starter_code?: string | null;
  tests?: string[];
};
'''
    new = '''export type HashMapPutStep = {
  code: string;
  key: string;
  value: string;
  hash_bits?: string;
  bucket: number;
  color?: string;
};

export type HashMapVisual = {
  kind: "hashmap";
  capacity?: number;
  init_code?: string;
  setup_lines?: string[];
  puts?: HashMapPutStep[];
  node_fields?: string[];
};

export type LessonScene = {
  id: string;
  type: SceneType;
  duration: number;
  narration: string;
  segments?: NarrationSegment[];
  expression?: TutorExpression;
  audio_url?: string | null;
  language?: string;
  filename?: string;
  code?: string;
  highlight_ranges?: HighlightRange[];
  expected_output?: string[];
  iterations?: ExecutionStep[];
  command?: string;
  stdout?: string[];
  stderr?: string;
  success?: boolean;
  verified?: boolean;
  kind?: string;
  question?: string;
  options?: string[];
  answer?: number | string | null;
  explanation?: string;
  bullets?: string[];
  diagram_steps?: { title: string; detail?: string; example?: string }[];
  visual_diagram?: HashMapVisual | null;
  takeaways?: string[];
  starter_code?: string | null;
  tests?: string[];
};
'''
    replace_once(path, old, new, "frontend HashMapVisual types")


def write_hashmap_board() -> None:
    path = ROOT / "frontend/components/player/HashMapBoard.tsx"
    path.write_text(
        '''"use client";

import { useMemo } from "react";
import { cn } from "@/lib/utils";
import type { HashMapPutStep, HashMapVisual } from "@/types/lesson";

export type HashMapBoardProps = {
  visual: HashMapVisual;
  activePutIndex: number;
  progress: number;
  topic: string;
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

export function HashMapBoard({ visual, activePutIndex, progress, topic }: HashMapBoardProps) {
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
      if (i === safeActive && p < 0.35) continue;
      const list = map.get(put.bucket) || [];
      list.push({ put, index: i });
      map.set(put.bucket, list);
    }
    return map;
  }, [puts, placedThrough, safeActive, p]);

  const activePut = safeActive >= 0 ? puts[safeActive] : null;
  const colliding = activePut ? isCollision(puts, safeActive) : false;
  const showEquals = Boolean(activePut && colliding && p >= 0.35 && p < 0.72);
  const formulaBucket = activePut?.bucket;

  return (
    <div className="hashmap-board relative flex min-h-0 flex-1 flex-col overflow-hidden rounded-2xl border border-cyan-200/20 bg-[#0b1220]/96 p-2.5 shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]">
      <div className="hashmap-board-grid pointer-events-none absolute inset-0" aria-hidden />

      {/* Top ~1/3: code + puts + formula */}
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
            const active = index === safeActive;
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
            {activePut?.hash_bits ? (
              <span className="truncate font-mono text-[10px] text-zinc-500">{activePut.hash_bits}</span>
            ) : null}
          </div>
          {showEquals ? (
            <p className="hashmap-equals mt-1 text-[10px] font-bold uppercase tracking-wide text-lime-300">
              equals? same bucket → chain via next
            </p>
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

      {/* Bottom ~2/3: buckets + nodes */}
      <div className="relative z-10 mt-2 flex min-h-0 flex-1 gap-2 overflow-hidden">
        <div className="hashmap-buckets flex w-[4.25rem] shrink-0 flex-col gap-0.5 overflow-y-auto pr-0.5">
          {Array.from({ length: capacity }).map((_, bucket) => {
            const filled = buckets.has(bucket);
            const active = activePut?.bucket === bucket && p >= 0.2;
            return (
              <div
                key={bucket}
                className={cn(
                  "hashmap-bucket flex h-[22px] items-center justify-between rounded-md border px-1.5 font-mono text-[10px] font-bold transition-all duration-300",
                  active
                    ? "border-cyan-300/70 bg-cyan-400/25 text-cyan-50 shadow-[0_0_12px_rgba(34,211,238,0.35)]"
                    : filled
                      ? "border-sky-300/35 bg-sky-400/15 text-sky-100"
                      : "border-sky-400/20 bg-sky-500/10 text-sky-200/80",
                )}
              >
                <span>{bucket}</span>
                <span className="text-[8px] font-semibold opacity-60">{filled ? "●" : ""}</span>
              </div>
            );
          })}
        </div>

        <div className="relative min-h-0 flex-1 overflow-y-auto">
          <div className="flex flex-col gap-1.5 pb-2">
            {Array.from({ length: capacity }).map((_, bucket) => {
              const chain = buckets.get(bucket);
              if (!chain?.length) return null;
              return (
                <div key={`chain-${bucket}`} className="flex flex-col gap-1" style={{ marginTop: bucket * 0.15 }}>
                  <p className="text-[9px] font-bold uppercase tracking-[0.14em] text-zinc-500">bucket {bucket}</p>
                  <div className="flex flex-col gap-1">
                    {chain.map(({ put, index }, chainIdx) => {
                      const t = tone(put.color);
                      const isNew = index === safeActive;
                      const slide = isNew ? clamp01((p - 0.35) / 0.45) : 1;
                      const nextExists = chainIdx < chain.length - 1;
                      return (
                        <div key={`${put.key}-${index}`} className="relative">
                          <div
                            className={cn(
                              "hashmap-node rounded-xl border bg-black/55 px-2 py-1.5 backdrop-blur-sm",
                              t.border,
                              isNew && t.glow,
                              isNew && "hashmap-node-enter",
                            )}
                            style={
                              isNew
                                ? {
                                    opacity: 0.35 + slide * 0.65,
                                    transform: `translateX(${(1 - slide) * 28}px) translateY(${(1 - slide) * -10}px) scale(${0.92 + slide * 0.08})`,
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
                            <div className="mt-1 grid grid-cols-2 gap-x-2 gap-y-0.5">
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
                            <div className="hashmap-next-arrow my-0.5 flex items-center gap-1 pl-3">
                              <span className="h-3 w-0.5 rounded-full bg-lime-400 shadow-[0_0_8px_rgba(163,230,53,0.8)]" />
                              <span className="text-[9px] font-extrabold uppercase tracking-wide text-lime-300">next →</span>
                            </div>
                          ) : null}
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
            {placedThrough < 0 ? (
              <p className="mt-6 text-center text-[11px] font-medium text-zinc-500">
                Empty table · capacity {capacity}
                <span className="mt-1 block text-[10px] text-zinc-600">{topic}</span>
              </p>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}
''',
        encoding="utf-8",
    )
    print(f"OK wrote {path.relative_to(ROOT)}")


def patch_reel_stage() -> None:
    path = ROOT / "frontend/components/player/ReelStage.tsx"
    text = path.read_text(encoding="utf-8")
    if "HashMapBoard" not in text:
        text = text.replace(
            'import { ExplainerFlow } from "@/components/player/ExplainerFlow";\n',
            'import { ExplainerFlow } from "@/components/player/ExplainerFlow";\n'
            'import { HashMapBoard } from "@/components/player/HashMapBoard";\n'
            'import type { HashMapVisual } from "@/types/lesson";\n',
            1,
        )
        path.write_text(text, encoding="utf-8")
        print("OK ReelStage: import HashMapBoard")
    else:
        print("SKIP ReelStage: HashMapBoard import")

    text = path.read_text(encoding="utf-8")
    if "hashmapVisual" not in text:
        old = '''  const diagramSteps = useMemo(() => {
    const steps = (scene.diagram_steps || [])
      .map((s) => ({
        title: String(s.title || "").trim(),
        detail: String(s.detail || "").trim(),
        example: String(s.example || "").trim(),
      }))
      .filter((s) => s.title);
    if (steps.length) return steps;
    return (scene.bullets || []).map((b) => ({ title: String(b || "").trim(), detail: "", example: "" })).filter((s) => s.title);
  }, [scene.diagram_steps, scene.bullets]);
  const stepTitles = useMemo(() => diagramSteps.map((s) => s.title), [diagramSteps]);
  const infoAnim = useMemo(
    () => (isConcept ? infoBulletAt(isExplainer ? stepTitles : scene.bullets || [], currentTime, duration) : null),
    [isConcept, isExplainer, stepTitles, scene.bullets, currentTime, duration],
  );
'''
        new = '''  const diagramSteps = useMemo(() => {
    const steps = (scene.diagram_steps || [])
      .map((s) => ({
        title: String(s.title || "").trim(),
        detail: String(s.detail || "").trim(),
        example: String(s.example || "").trim(),
      }))
      .filter((s) => s.title);
    if (steps.length) return steps;
    return (scene.bullets || []).map((b) => ({ title: String(b || "").trim(), detail: "", example: "" })).filter((s) => s.title);
  }, [scene.diagram_steps, scene.bullets]);
  const hashmapVisual = useMemo((): HashMapVisual | null => {
    const raw = scene.visual_diagram;
    if (raw && raw.kind === "hashmap") return raw;
    const blob = `${lesson.topic || ""} ${topic || ""}`.toLowerCase();
    if (isExplainer && /hash\\s*map|hashtable|hash\\s*table/.test(blob)) {
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
  const syncTitles = putTitles.length ? putTitles : isExplainer ? stepTitles : scene.bullets || [];
  const infoAnim = useMemo(
    () => (isConcept ? infoBulletAt(syncTitles, currentTime, duration) : null),
    [isConcept, syncTitles, currentTime, duration],
  );
  const putProgress = useMemo(() => {
    if (!infoAnim || !infoAnim.beats.length) return 1;
    const beat = infoAnim.beats[Math.max(0, Math.min(infoAnim.active, infoAnim.beats.length - 1))];
    if (!beat) return 1;
    const span = Math.max(0.05, beat.end - beat.start);
    return Math.max(0, Math.min(1, (currentTime - beat.start) / span));
  }, [infoAnim, currentTime]);
'''
        replace_once(path, old, new, "ReelStage hashmap visual + sync")
    else:
        print("SKIP ReelStage: hashmapVisual already present")

    text = path.read_text(encoding="utf-8")
    if "hashmapVisual ?" not in text and "<HashMapBoard" not in text:
        old_render = '''          <div className="relative z-10 flex min-h-0 flex-1 flex-col items-stretch justify-center py-2">
            {isExplainer && diagramSteps.length ? (
              <ExplainerFlow
                steps={diagramSteps}
                active={infoAnim?.active ?? 0}
                visibleCount={infoAnim?.visibleCount ?? 0}
                topic={topic}
              />
            ) : (
'''
        new_render = '''          <div className="relative z-10 flex min-h-0 flex-1 flex-col items-stretch justify-center py-2">
            {isExplainer && hashmapVisual ? (
              <HashMapBoard
                visual={hashmapVisual}
                activePutIndex={infoAnim?.active ?? 0}
                progress={putProgress}
                topic={topic}
              />
            ) : isExplainer && diagramSteps.length ? (
              <ExplainerFlow
                steps={diagramSteps}
                active={infoAnim?.active ?? 0}
                visibleCount={infoAnim?.visibleCount ?? 0}
                topic={topic}
              />
            ) : (
'''
        replace_once(path, old_render, new_render, "ReelStage render HashMapBoard")
    else:
        print("SKIP ReelStage: HashMapBoard render")


def patch_planner() -> None:
    path = ROOT / "backend/app/agents/topic_mode.py"
    text = path.read_text(encoding="utf-8")
    if "visual_diagram" in text and "default_hashmap_visual" in text:
        print("SKIP topic_mode: visual_diagram already present")
    else:
        # Add helper + update instruction
        if "def default_hashmap_visual" not in text:
            insert_at = text.index("def explainer_reel_planner_instruction")
            helper = '''def topic_is_hashmap(topic: str) -> bool:
    blob = (topic or "").casefold()
    return bool(
        re.search(r"hash\\s*map|hashtable|hash\\s*table|map\\s+internals|internal.*map", blob)
    )


def default_hashmap_visual() -> dict:
    """Phone-friendly HashMap board demo (capacity 8, one collision)."""
    return {
        "kind": "hashmap",
        "capacity": 8,
        "init_code": "Map<String,Integer> map = new HashMap<>();",
        "setup_lines": [],
        "puts": [
            {
                "code": 'map.put("Mia",95)',
                "key": "Mia",
                "value": "95",
                "hash_bits": "1010",
                "bucket": 2,
                "color": "orange",
            },
            {
                "code": 'map.put("Leo",88)',
                "key": "Leo",
                "value": "88",
                "hash_bits": "0101",
                "bucket": 5,
                "color": "blue",
            },
            {
                "code": 'map.put("Zoe",92)',
                "key": "Zoe",
                "value": "92",
                "hash_bits": "1010",
                "bucket": 2,
                "color": "green",
            },
        ],
        "node_fields": ["key", "value", "hash", "next"],
    }


'''
            text = text[:insert_at] + helper + text[insert_at:]
            path.write_text(text, encoding="utf-8")
            print("OK topic_mode: default_hashmap_visual helper")

        text = path.read_text(encoding="utf-8")
        old = '''- Concept ({span(14, 18)}): Narrate HOW it works. MUST include 4-6 diagram_steps — each is a MECHANISM stage.
  Example for HashMap: Key → hashCode → bucket index → store entry → collision handling → O(1) get.
  Also fill bullets with the diagram_steps titles (for older UI).
  Each diagram_step MUST be {{"title": "...", "detail": "...", "example": "..."}}.
  - title: max ~6 words; detail: one short clause.
  - example: REQUIRED — a tiny concrete snippet OR everyday analogy the viewer can relate to (1 line, under ~60 chars).
    Coding topics: micro code fragment only, e.g. `new Student()`, `obj = null`, `map.put("a",1)` hash path.
    NOT a full Main.java program, NOT a for-loop demo lesson, NOT multi-line runnable scenes.
  Short examples ON the diagram are allowed; full runnable program scenes are still forbidden.
'''
        new = '''- Concept ({span(14, 18)}): Narrate HOW it works. MUST include 4-6 diagram_steps — each is a MECHANISM stage.
  Example for HashMap: empty buckets → node structure → put1 → put2 → collision put → takeaway.
  Also fill bullets with the diagram_steps titles (for older UI).
  Each diagram_step MUST be {{"title": "...", "detail": "...", "example": "..."}}.
  - title: max ~6 words; detail: one short clause.
  - example: REQUIRED — a tiny concrete snippet OR everyday analogy the viewer can relate to (1 line, under ~60 chars).
    Coding topics: micro code fragment only, e.g. `new Student()`, `obj = null`, `map.put("a",1)` hash path.
    NOT a full Main.java program, NOT a for-loop demo lesson, NOT multi-line runnable scenes.
  Short examples ON the diagram are allowed; full runnable program scenes are still forbidden.
- HASHMAP / hashtable / map-internals topics: MUST also fill concept.visual_diagram with kind "hashmap":
  - capacity: prefer 8 (phone-readable), not 16
  - init_code: e.g. Map<String,Integer> map = new HashMap<>();
  - setup_lines: optional short lines; prefer short string keys (Mia/Leo/Zoe) OR short labels (e1/Dev)
  - puts: 3–4 concrete put steps with colors (orange|blue|green), hash_bits, bucket indices
  - MUST include at least one collision (two puts same bucket) so next-chain is visible
  - node_fields: ["key","value","hash","next"]
  Concept narration should walk the puts. For non-hashmap explainer topics, visual_diagram may be null.
'''
        replace_once(path, old, new, "explainer planner hashmap visual_diagram rules")


def patch_orchestrator() -> None:
    path = ROOT / "backend/app/agents/orchestrator.py"
    text = path.read_text(encoding="utf-8")
    if "default_hashmap_visual" not in text:
        old_imp = '''from app.agents.topic_mode import (
    explainer_reel_planner_instruction,
'''
        # find actual import block
        if "from app.agents.topic_mode import" in text:
            # Read the import section
            pass
        # Safer: patch after imports of topic_mode
        import_old = None
        for line in text.splitlines():
            if "from app.agents.topic_mode import" in line or (
                import_old is not None and line.strip().startswith(")")
            ):
                pass
        # Use a targeted replace on the known import
        old = '''    explainer_reel_planner_instruction,
'''
        if "default_hashmap_visual" not in text:
            # Find the topic_mode import block
            start = text.find("from app.agents.topic_mode import")
            if start < 0:
                raise SystemExit("topic_mode import missing in orchestrator")
            end = text.find(")", start)
            block = text[start : end + 1]
            if "default_hashmap_visual" not in block:
                new_block = block.rstrip(")") + "    default_hashmap_visual,\n    topic_is_hashmap,\n)"
                # Fix if already has trailing comma style
                if block.rstrip().endswith(","):
                    new_block = block[:-1] + "    default_hashmap_visual,\n    topic_is_hashmap,\n)"
                else:
                    # insert before closing paren
                    inner = block[len("from app.agents.topic_mode import") :].strip()
                    if inner.startswith("("):
                        new_block = (
                            "from app.agents.topic_mode import (\n"
                            + "\n".join(
                                "    " + x.strip().rstrip(",") + ","
                                for x in block[block.index("(") + 1 : block.rindex(")")].split(",")
                                if x.strip()
                            )
                            + "\n    default_hashmap_visual,\n    topic_is_hashmap,\n)"
                        )
                    else:
                        new_block = block
                text = text[:start] + new_block + text[end + 1 :]
                path.write_text(text, encoding="utf-8")
                print("OK orchestrator: import default_hashmap_visual")
    else:
        print("SKIP orchestrator: imports")

    # Re-read and fix import more carefully if broken
    text = path.read_text(encoding="utf-8")
    start = text.find("from app.agents.topic_mode import")
    end = text.find("\n\n", start)
    block = text[start:end]
    if "default_hashmap_visual" not in block or "topic_is_hashmap" not in block:
        # Rewrite cleanly
        # parse names
        if "(" in block:
            names = [
                n.strip().rstrip(",")
                for n in block[block.index("(") + 1 : block.rindex(")")].splitlines()
                if n.strip() and n.strip() != ")"
            ]
            names = [n.split("#")[0].strip().rstrip(",") for n in names if n.strip().rstrip(",")]
        else:
            names = [block.split("import", 1)[1].strip()]
        for extra in ("default_hashmap_visual", "topic_is_hashmap"):
            if extra not in names:
                names.append(extra)
        new_block = "from app.agents.topic_mode import (\n" + "".join(f"    {n},\n" for n in names) + ")"
        # find exact end of import (closing paren line)
        end_paren = text.find(")", start)
        text = text[:start] + new_block + text[end_paren + 1 :]
        path.write_text(text, encoding="utf-8")
        print("OK orchestrator: cleaned topic_mode imports")

    text = path.read_text(encoding="utf-8")
    if "visual_diagram" in text and "default_hashmap_visual()" in text:
        print("SKIP orchestrator: visual_diagram synthesis already present")
        return

    old = '''            if scene.type == "concept":
                steps = list(getattr(scene, "diagram_steps", None) or [])
                bullets = list(getattr(scene, "bullets", None) or [])
                # Only synthesize diagram_steps for Explainer mode so Info reels keep bullet UI.
                if getattr(lesson, "reel_mode", None) == "explainer" and not steps and bullets:
                    patch["diagram_steps"] = [
                        DiagramStep(title=str(b)[:120], detail="") for b in bullets if str(b).strip()
                    ]
                elif steps and not bullets:
                    patch["bullets"] = [
                        (getattr(s, "title", None) or (s.get("title") if isinstance(s, dict) else str(s)))[:120]
                        for s in steps
                    ]
'''
    new = '''            if scene.type == "concept":
                steps = list(getattr(scene, "diagram_steps", None) or [])
                bullets = list(getattr(scene, "bullets", None) or [])
                # Only synthesize diagram_steps for Explainer mode so Info reels keep bullet UI.
                if getattr(lesson, "reel_mode", None) == "explainer" and not steps and bullets:
                    patch["diagram_steps"] = [
                        DiagramStep(title=str(b)[:120], detail="") for b in bullets if str(b).strip()
                    ]
                elif steps and not bullets:
                    patch["bullets"] = [
                        (getattr(s, "title", None) or (s.get("title") if isinstance(s, dict) else str(s)))[:120]
                        for s in steps
                    ]
                # HashMap explainer: never fall back to list UI — synthesize board if planner omitted it.
                if getattr(lesson, "reel_mode", None) == "explainer" and topic_is_hashmap(
                    getattr(lesson, "topic", "") or ""
                ):
                    existing = getattr(scene, "visual_diagram", None)
                    kind = getattr(existing, "kind", None) if existing is not None else (
                        existing.get("kind") if isinstance(existing, dict) else None
                    )
                    if kind != "hashmap":
                        from app.schemas.lesson import HashMapVisual

                        patch["visual_diagram"] = HashMapVisual.model_validate(default_hashmap_visual())
'''
    replace_once(path, old, new, "orchestrator synthesize HashMapVisual")


def patch_css() -> None:
    path = ROOT / "frontend/app/globals.css"
    text = path.read_text(encoding="utf-8")
    if ".hashmap-board" in text:
        print("SKIP globals.css: hashmap styles present")
        return
    css = '''

/* HashMap whiteboard board (explainer) */
.hashmap-board-grid {
  background-image:
    linear-gradient(rgba(34, 211, 238, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(34, 211, 238, 0.045) 1px, transparent 1px);
  background-size: 22px 22px;
  mask-image: radial-gradient(ellipse at center, black 40%, transparent 85%);
}

.hashmap-put-pill {
  max-width: 100%;
}

.hashmap-node-enter {
  will-change: transform, opacity;
  transition: transform 0.35s cubic-bezier(0.22, 1, 0.36, 1), opacity 0.35s ease;
}

.hashmap-next-arrow {
  animation: hashmap-next-pulse 1.1s ease-in-out infinite;
}

@keyframes hashmap-next-pulse {
  0%,
  100% {
    opacity: 0.75;
    filter: drop-shadow(0 0 2px rgba(163, 230, 53, 0.4));
  }
  50% {
    opacity: 1;
    filter: drop-shadow(0 0 8px rgba(163, 230, 53, 0.9));
  }
}

.hashmap-equals {
  animation: hashmap-equals-flash 0.9s ease-in-out infinite alternate;
}

@keyframes hashmap-equals-flash {
  from {
    opacity: 0.7;
  }
  to {
    opacity: 1;
  }
}

.hashmap-bucket {
  min-height: 22px;
}
'''
    path.write_text(text.rstrip() + "\n" + css, encoding="utf-8")
    print("OK globals.css: hashmap styles")


def patch_export() -> None:
    path = ROOT / "frontend/lib/reelExport.ts"
    text = path.read_text(encoding="utf-8")
    if "drawHashMapBoard" in text:
        print("SKIP reelExport: drawHashMapBoard already present")
        return

    # Insert drawHashMapBoard before drawConceptPanel
    helper = r'''
function drawHashMapBoard(
  ctx: CanvasRenderingContext2D,
  scene: LessonScene,
  elapsed: number,
  duration: number,
  topic: string,
  lesson?: Lesson,
) {
  const visual = (scene.visual_diagram && scene.visual_diagram.kind === "hashmap"
    ? scene.visual_diagram
    : {
        kind: "hashmap" as const,
        capacity: 8,
        init_code: "Map<String,Integer> map = new HashMap<>();",
        setup_lines: [] as string[],
        puts: [
          { code: 'map.put("Mia",95)', key: "Mia", value: "95", hash_bits: "1010", bucket: 2, color: "orange" },
          { code: 'map.put("Leo",88)', key: "Leo", value: "88", hash_bits: "0101", bucket: 5, color: "blue" },
          { code: 'map.put("Zoe",92)', key: "Zoe", value: "92", hash_bits: "1010", bucket: 2, color: "green" },
        ],
      });
  const puts = visual.puts || [];
  const capacity = Math.max(4, Math.min(32, visual.capacity ?? 8));
  const titles = puts.map((p) => p.code || p.key);
  const anim = infoBulletAt(titles, elapsed, duration);
  const active = Math.max(0, Math.min(anim.active, Math.max(0, puts.length - 1)));
  const beat = anim.beats[active];
  const progress = beat ? Math.max(0, Math.min(1, (elapsed - beat.start) / Math.max(0.05, beat.end - beat.start))) : 1;

  const footer = 220;
  const headerBottom = 168;
  const available = HEIGHT - footer - headerBottom;
  const panelH = Math.min(available, 560);
  const panelTop = headerBottom + Math.max(0, (available - panelH) / 2);
  const x = 28;
  const w = WIDTH - 108;

  ctx.textAlign = "center";
  ctx.fillStyle = "rgba(103,232,249,0.95)";
  ctx.font = "700 16px ui-sans-serif, system-ui";
  ctx.fillText("EXPLAINER", WIDTH / 2, 78);
  ctx.fillStyle = "#ffffff";
  ctx.font = "700 26px ui-sans-serif, system-ui";
  wrapLines(ctx, topic, WIDTH - 120, 2).forEach((line, index) => {
    ctx.fillText(line, WIDTH / 2, 112 + index * 30);
  });
  ctx.textAlign = "left";

  roundRect(ctx, x, panelTop, w, panelH, 22);
  ctx.fillStyle = "rgba(11,18,32,0.96)";
  ctx.fill();
  ctx.strokeStyle = "rgba(34,211,238,0.28)";
  ctx.lineWidth = 1.5;
  ctx.stroke();

  let y = panelTop + 16;
  // init code
  roundRect(ctx, x + 14, y, w - 28, 28, 10);
  ctx.fillStyle = "rgba(16,185,129,0.18)";
  ctx.fill();
  ctx.strokeStyle = "rgba(52,211,153,0.4)";
  ctx.stroke();
  ctx.fillStyle = "#d1fae5";
  ctx.font = "600 13px ui-monospace, monospace";
  ctx.fillText(String(visual.init_code || "").slice(0, 42), x + 24, y + 19);
  y += 40;

  // put chips
  const colors: Record<string, string> = {
    orange: "#f97316",
    blue: "#0ea5e9",
    green: "#10b981",
    amber: "#fbbf24",
    cyan: "#22d3ee",
  };
  let chipX = x + 14;
  puts.forEach((put, index) => {
    const label = String(put.code || put.key).slice(0, 22);
    ctx.font = "700 11px ui-monospace, monospace";
    const tw = ctx.measureText(label).width + 18;
    const activeChip = index === active;
    const past = index < active;
    roundRect(ctx, chipX, y, tw, 22, 11);
    ctx.fillStyle = activeChip || past ? colors[(put.color || "orange").toLowerCase()] || "#f97316" : "rgba(255,255,255,0.08)";
    ctx.globalAlpha = activeChip ? 1 : past ? 0.7 : 0.45;
    ctx.fill();
    ctx.globalAlpha = 1;
    ctx.fillStyle = activeChip || past ? "#09090b" : "#a1a1aa";
    ctx.fillText(label, chipX + 9, y + 15);
    chipX += tw + 8;
  });
  y += 34;

  // formula
  roundRect(ctx, x + 14, y, w - 28, 44, 12);
  ctx.fillStyle = "rgba(0,0,0,0.4)";
  ctx.fill();
  ctx.fillStyle = "#a1a1aa";
  ctx.font = "700 10px ui-sans-serif, system-ui";
  ctx.fillText("put(K,V)  →  hash(k)  →  index = hash & (n-1)", x + 24, y + 16);
  const bucket = puts[active]?.bucket ?? 0;
  const collision = puts.slice(0, active).some((p) => p.bucket === bucket);
  ctx.beginPath();
  ctx.arc(x + 36, y + 32, 10, 0, Math.PI * 2);
  ctx.fillStyle = collision && progress > 0.35 && progress < 0.72 ? "#a3e635" : "#22d3ee";
  ctx.fill();
  ctx.fillStyle = "#09090b";
  ctx.font = "800 11px ui-sans-serif, system-ui";
  ctx.textAlign = "center";
  ctx.fillText(String(bucket), x + 36, y + 36);
  ctx.textAlign = "left";
  if (collision && progress > 0.35 && progress < 0.72) {
    ctx.fillStyle = "#bef264";
    ctx.font = "700 11px ui-sans-serif, system-ui";
    ctx.fillText("equals? same bucket → chain via next", x + 56, y + 36);
  }
  y += 56;

  // buckets + nodes
  const bucketW = 52;
  const bucketH = Math.min(22, (panelTop + panelH - y - 16) / capacity - 2);
  const placedThrough = progress < 0.35 ? active - 1 : active;
  const chains = new Map<number, typeof puts>();
  for (let i = 0; i <= placedThrough; i++) {
    const put = puts[i];
    if (!put) continue;
    const list = chains.get(put.bucket) || [];
    list.push(put);
    chains.set(put.bucket, list);
  }

  for (let b = 0; b < capacity; b++) {
    const by = y + b * (bucketH + 2);
    const filled = chains.has(b);
    const isActive = puts[active]?.bucket === b && progress >= 0.2;
    roundRect(ctx, x + 14, by, bucketW, bucketH, 6);
    ctx.fillStyle = isActive ? "rgba(34,211,238,0.3)" : filled ? "rgba(56,189,248,0.18)" : "rgba(56,189,248,0.1)";
    ctx.fill();
    ctx.strokeStyle = isActive ? "rgba(103,232,249,0.7)" : "rgba(56,189,248,0.25)";
    ctx.stroke();
    ctx.fillStyle = "#e0f2fe";
    ctx.font = "700 10px ui-monospace, monospace";
    ctx.fillText(String(b), x + 22, by + bucketH * 0.68);
  }

  // draw chains to the right of buckets
  const nodeX = x + 14 + bucketW + 12;
  for (const [b, chain] of chains.entries()) {
    let ny = y + b * (bucketH + 2);
    chain.forEach((put, idx) => {
      const nh = 52;
      const isNew = puts[active] === put;
      const slide = isNew ? Math.max(0, Math.min(1, (progress - 0.35) / 0.45)) : 1;
      const ox = isNew ? (1 - slide) * 24 : 0;
      roundRect(ctx, nodeX + ox, ny, w - (nodeX - x) - 20, nh, 10);
      ctx.globalAlpha = 0.4 + slide * 0.6;
      ctx.fillStyle = "rgba(0,0,0,0.55)";
      ctx.fill();
      ctx.strokeStyle = colors[(put.color || "orange").toLowerCase()] || "#f97316";
      ctx.lineWidth = 1.5;
      ctx.stroke();
      ctx.globalAlpha = 1;
      ctx.fillStyle = "#fff";
      ctx.font = "800 12px ui-monospace, monospace";
      ctx.fillText(put.key, nodeX + ox + 10, ny + 16);
      ctx.fillStyle = "#a1a1aa";
      ctx.font = "600 10px ui-monospace, monospace";
      ctx.fillText(`val ${put.value}  hash ${put.hash_bits || "—"}`, nodeX + ox + 10, ny + 32);
      const nextLabel = idx < chain.length - 1 ? `next → ${chain[idx + 1].key}` : "next → null";
      ctx.fillStyle = idx < chain.length - 1 ? "#bef264" : "#71717a";
      ctx.fillText(nextLabel, nodeX + ox + 10, ny + 46);
      if (idx < chain.length - 1) {
        ctx.strokeStyle = "#a3e635";
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(nodeX + 18, ny + nh + 2);
        ctx.lineTo(nodeX + 18, ny + nh + 8);
        ctx.stroke();
      }
      ny += nh + 10;
    });
  }
}

'''
    marker = "function drawConceptPanel("
    if marker not in text:
        raise SystemExit("drawConceptPanel missing")
    text = text.replace(marker, helper + marker, 1)

    # Branch at start of drawConceptPanel body to use hashmap board
    old_branch = '''function drawConceptPanel(
  ctx: CanvasRenderingContext2D,
  scene: LessonScene,
  elapsed: number,
  duration: number,
  topic: string,
  lesson?: Lesson,
) {
  const footer = 220;
'''
    new_branch = '''function drawConceptPanel(
  ctx: CanvasRenderingContext2D,
  scene: LessonScene,
  elapsed: number,
  duration: number,
  topic: string,
  lesson?: Lesson,
) {
  const explainerMode =
    lesson?.reel_mode === "explainer" || Boolean(scene.diagram_steps && scene.diagram_steps.length);
  const wantsHashMap =
    (scene.visual_diagram && scene.visual_diagram.kind === "hashmap") ||
    (explainerMode && /hash\\s*map|hashtable|hash\\s*table/i.test(`${lesson?.topic || ""} ${topic || ""}`));
  if (wantsHashMap) {
    drawHashMapBoard(ctx, scene, elapsed, duration, topic, lesson);
    return;
  }
  const footer = 220;
'''
    if "wantsHashMap" not in text:
        text = text.replace(old_branch, new_branch, 1)
    path.write_text(text, encoding="utf-8")
    print("OK reelExport: drawHashMapBoard")


def main() -> None:
    patch_schema()
    patch_frontend_types()
    write_hashmap_board()
    patch_reel_stage()
    patch_planner()
    patch_orchestrator()
    patch_css()
    patch_export()
    print("DONE patch_hashmap_board")


if __name__ == "__main__":
    main()
