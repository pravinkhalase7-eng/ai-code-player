#!/usr/bin/env python3
"""Focus-stage Explainer + diagram_step.example across schema/UI/planner/export/DB."""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

ROOT = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder")


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        if new in text or (label and label in text and old.strip()[:40] not in text):
            # idempotent: already applied
            print(f"SKIP {path.name}: {label} (already applied or missing)")
            return
        raise SystemExit(f"MISSING in {path}: {label}\n---\n{old[:200]}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"OK {path.relative_to(ROOT)}: {label}")


def write_explainer_flow() -> None:
    path = ROOT / "frontend/components/player/ExplainerFlow.tsx"
    path.write_text(
        '''"use client";

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
  if (/\\b(interface|ui|window|panel|screen)\\b/.test(t)) return AppWindow;
  if (/\\b(lambda|function|fn\\b|closure)\\b/.test(t)) return SquareFunction;
  if (/\\b(bytecode|binary|byte|opcode|asm)\\b/.test(t)) return Binary;
  if (/\\b(factory|builder|create|construct|निर्माण|new)\\b/.test(t)) return Factory;
  if (/\\b(call|invoke|dispatch|phone)\\b/.test(t)) return PhoneCall;
  if (/\\b(hash|digest|checksum)\\b/.test(t)) return Hash;
  if (/\\b(bucket|map|dict|table|store|db|database)\\b/.test(t)) return Database;
  if (/\\b(key|lookup|index)\\b/.test(t)) return Key;
  if (/\\b(value|payload|data|object|ऑब्जेक्ट)\\b/.test(t)) return Box;
  if (/\\b(memory|heap|stack|ram|cache|sweep|मार्किंग|स्वीप|मेमोरी|हिप)\\b/.test(t)) return MemoryStick;
  if (/\\b(package|module|import)\\b/.test(t)) return Package;
  if (/\\b(cpu|runtime|vm|process|gc|गारबेज)\\b/.test(t)) return Cpu;
  if (/\\b(layer|pipeline|stage)\\b/.test(t)) return Layers;
  if (/\\b(flow|pipeline|workflow|graph)\\b/.test(t)) return Workflow;
  if (/\\b(code|source|script)\\b/.test(t)) return FileCode;
  if (/\\b(brace|syntax|parse)\\b/.test(t)) return Braces;
  if (/\\b(spark|fast|power|energy)\\b/.test(t)) return Zap;
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

      <div className="relative z-10 flex min-h-0 flex-1 flex-col gap-3">
        {/* Mini pipeline */}
        <div className="explainer-mini-pipeline relative mx-auto w-full max-w-[22rem] shrink-0 px-2 pt-1">
          <div className="pointer-events-none absolute left-4 right-4 top-1/2 h-[2px] -translate-y-1/2 rounded-full bg-cyan-400/15" aria-hidden />
          <div
            className="pointer-events-none absolute left-4 top-1/2 h-[2px] -translate-y-1/2 rounded-full bg-gradient-to-r from-cyan-400/70 via-amber-300/80 to-cyan-300/50 transition-[width] duration-500 ease-out"
            style={{ width: `calc((100% - 2rem) * ${tokenPct / 100})` }}
            aria-hidden
          />
          <div
            className="explainer-token pointer-events-none absolute top-1/2 z-20 -translate-y-1/2 transition-[left] duration-500 ease-out"
            style={{ left: `calc(1rem + (100% - 2rem) * ${tokenPct / 100})`, transform: "translate(-50%, -50%)" }}
            aria-hidden
          >
            <span className="explainer-token-orb" />
          </div>
          <ol className="relative z-10 flex items-center justify-between gap-1">
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
                    "explainer-mini-node flex h-8 w-8 items-center justify-center rounded-full border transition-all duration-300",
                    isActive && "is-active border-amber-300/80 bg-amber-400/25 text-amber-100 shadow-[0_0_16px_rgba(251,191,36,0.45)]",
                    isPast && !isActive && "border-cyan-300/50 bg-cyan-400/30 text-cyan-50",
                    isFuture && !isActive && "border-white/10 bg-white/5 text-cyan-200/35 opacity-45",
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
            className="explainer-stage-card relative mx-auto flex w-full max-w-[22rem] flex-col gap-3 rounded-2xl border border-cyan-300/45 bg-[rgba(8,51,68,0.82)] px-3.5 py-3.5 shadow-[0_0_0_1px_rgba(34,211,238,0.28),0_16px_40px_rgba(8,145,178,0.35)] backdrop-blur-md"
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
''',
        encoding="utf-8",
    )
    print(f"OK wrote {path.relative_to(ROOT)}")


def patch_schema() -> None:
    path = ROOT / "backend/app/schemas/lesson.py"
    text = path.read_text(encoding="utf-8")
    old = (
        "class DiagramStep(BaseModel):\n"
        "    title: str = Field(min_length=1, max_length=120)\n"
        '    detail: str = Field(default="", max_length=240)\n'
    )
    new = (
        "class DiagramStep(BaseModel):\n"
        "    title: str = Field(min_length=1, max_length=120)\n"
        '    detail: str = Field(default="", max_length=240)\n'
        '    example: str = Field(default="", max_length=160)\n'
    )
    if "example: str = Field(default=\"\", max_length=160)" in text:
        print("SKIP schema: example already present")
        return
    if old not in text:
        raise SystemExit("DiagramStep block missing in lesson.py")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print("OK schema DiagramStep.example")


def patch_planner() -> None:
    path = ROOT / "backend/app/agents/topic_mode.py"
    old = '''Required scenes IN THIS ORDER: intro, concept, summary.
Do NOT include code, execution, terminal, or quiz scenes.
Do NOT invent fake code, Main.java, for-loops, put/get demos, print statements, or sandbox output.
Do NOT teach how to call an API — teach the internal mechanism stages.

Hard rules:
- Intro ({span(6, 8)}): Hook with a misconception (e.g. "HashMap is just magic O(1)"). Never open with stop scrolling.
- Concept ({span(14, 18)}): Narrate HOW it works. MUST include 4-6 diagram_steps — each is a MECHANISM stage with title + short detail.
  Example for HashMap: Key → hashCode → bucket index → store entry → collision handling → O(1) get.
  Also fill bullets with the diagram_steps titles (for older UI).
  Each diagram_step: {{"title": "...", "detail": "..."}} — title max ~6 words, detail one short clause.
- Summary ({span(4, 6)}): One punchy takeaway about the mechanism. 2-3 short takeaways. Ask them to follow / save / comment.
- Spoken style: short sentences, catchy, not a lecture. No filler.
- Never say "{target} seconds" or "in this short" in narration or titles.
- spoken_language must match the tutor plan for all spoken lines, bullets, diagram_steps, takeaways, and the title.
- lesson_id should be a short slug.
- language may stay as requested for metadata, but there is no program.
'''.strip()

    # Use a regex-friendly approach on the function body instead
    text = path.read_text(encoding="utf-8")
    start = text.find("def explainer_reel_planner_instruction")
    if start < 0:
        raise SystemExit("explainer_reel_planner_instruction missing")
    end = text.find("\n\n", start + 10)
    # find end of function return string — easier to replace specific lines
    old_ban = "Do NOT invent fake code, Main.java, for-loops, put/get demos, print statements, or sandbox output."
    new_ban = (
        "Do NOT invent full runnable programs, Main.java classes, for-loop demos, print/sandbox output, or API-usage tutorials.\n"
        "Tiny 1-line micro-examples ON diagram_steps.example are REQUIRED (see below) — those are not \"fake code programs\"."
    )
    if "diagram_steps.example" in text[start:start+2500]:
        print("SKIP planner: example instruction already present")
    else:
        if old_ban not in text:
            raise SystemExit("planner ban line missing")
        # Only replace inside explainer function (second occurrence after info reel)
        idx = text.find(old_ban, start)
        if idx < 0:
            raise SystemExit("ban line not in explainer fn")
        text = text[:idx] + new_ban + text[idx + len(old_ban):]

    old_concept = (
        '- Concept ({span(14, 18)}): Narrate HOW it works. MUST include 4-6 diagram_steps — each is a MECHANISM stage with title + short detail.\n'
        '  Example for HashMap: Key → hashCode → bucket index → store entry → collision handling → O(1) get.\n'
        '  Also fill bullets with the diagram_steps titles (for older UI).\n'
        '  Each diagram_step: {{"title": "...", "detail": "..."}} — title max ~6 words, detail one short clause.'
    )
    new_concept = (
        '- Concept ({span(14, 18)}): Narrate HOW it works. MUST include 4-6 diagram_steps — each is a MECHANISM stage.\n'
        '  Example for HashMap: Key → hashCode → bucket index → store entry → collision handling → O(1) get.\n'
        '  Also fill bullets with the diagram_steps titles (for older UI).\n'
        '  Each diagram_step MUST be {{"title": "...", "detail": "...", "example": "..."}}.\n'
        '  - title: max ~6 words; detail: one short clause.\n'
        '  - example: REQUIRED — a tiny concrete snippet OR everyday analogy the viewer can relate to (1 line, under ~60 chars).\n'
        '    Coding topics: micro code fragment only, e.g. `new Student()`, `obj = null`, `map.put("a",1)` hash path.\n'
        '    NOT a full Main.java program, NOT a for-loop demo lesson, NOT multi-line runnable scenes.\n'
        '  Short examples ON the diagram are allowed; full runnable program scenes are still forbidden.'
    )
    if "example\": \"...\"" in text[start:start + 3000] or '"example": "..."' in text[start:start + 3000]:
        # check more carefully
        pass
    if 'MUST be {{"title": "...", "detail": "...", "example": "..."}}' in text:
        print("SKIP planner concept block already updated")
    else:
        if old_concept not in text:
            raise SystemExit("concept block missing in planner")
        text = text.replace(old_concept, new_concept, 1)

    # spoken_language line — mention example
    old_spoken = (
        "- spoken_language must match the tutor plan for all spoken lines, bullets, diagram_steps, takeaways, and the title."
    )
    new_spoken = (
        "- spoken_language must match the tutor plan for all spoken lines, bullets, diagram_steps (title/detail; keep code tokens in example), takeaways, and the title."
    )
    # only in explainer section — find after start
    idx = text.find(old_spoken, start)
    if idx >= 0 and "keep code tokens in example" not in text[start:start+3500]:
        text = text[:idx] + new_spoken + text[idx + len(old_spoken):]

    path.write_text(text, encoding="utf-8")
    print("OK planner explainer_reel_planner_instruction")


def patch_orchestrator() -> None:
    path = ROOT / "backend/app/agents/orchestrator.py"
    text = path.read_text(encoding="utf-8")

    old_gather = '''        for step in list(getattr(scene, "diagram_steps", None) or []):
            title = getattr(step, "title", None) or (step.get("title") if isinstance(step, dict) else None)
            detail = getattr(step, "detail", None) or (step.get("detail") if isinstance(step, dict) else None)
            if title:
                texts.append(str(title))
            if detail:
                texts.append(str(detail))'''
    new_gather = '''        for step in list(getattr(scene, "diagram_steps", None) or []):
            title = getattr(step, "title", None) or (step.get("title") if isinstance(step, dict) else None)
            detail = getattr(step, "detail", None) or (step.get("detail") if isinstance(step, dict) else None)
            example = getattr(step, "example", None) or (step.get("example") if isinstance(step, dict) else None)
            if title:
                texts.append(str(title))
            if detail:
                texts.append(str(detail))
            if example:
                texts.append(str(example))'''
    if "if example:" in text and "texts.append(str(example))" in text:
        print("SKIP gather: example already")
    else:
        if old_gather not in text:
            raise SystemExit("gather_teaching_texts diagram block missing")
        text = text.replace(old_gather, new_gather, 1)

    old_scatter = '''            rebuilt = []
            for step in steps:
                raw_title = getattr(step, "title", None) if not isinstance(step, dict) else step.get("title")
                raw_detail = getattr(step, "detail", None) if not isinstance(step, dict) else step.get("detail")
                # Mirror gather_teaching_texts: emit title if truthy, detail if truthy.
                title = next(cursor)[:120] if raw_title else str(raw_title or "Step")[:120]
                detail = next(cursor)[:240] if raw_detail else ""
                rebuilt.append(DiagramStep(title=title or "Step", detail=detail))
            updates["diagram_steps"] = rebuilt'''
    new_scatter = '''            rebuilt = []
            for step in steps:
                raw_title = getattr(step, "title", None) if not isinstance(step, dict) else step.get("title")
                raw_detail = getattr(step, "detail", None) if not isinstance(step, dict) else step.get("detail")
                raw_example = getattr(step, "example", None) if not isinstance(step, dict) else step.get("example")
                # Mirror gather_teaching_texts: emit title/detail/example if truthy.
                title = next(cursor)[:120] if raw_title else str(raw_title or "Step")[:120]
                detail = next(cursor)[:240] if raw_detail else ""
                example = next(cursor)[:160] if raw_example else ""
                rebuilt.append(DiagramStep(title=title or "Step", detail=detail, example=example))
            updates["diagram_steps"] = rebuilt'''
    if "raw_example" in text:
        print("SKIP scatter: example already")
    else:
        if old_scatter not in text:
            raise SystemExit("scatter diagram block missing")
        text = text.replace(old_scatter, new_scatter, 1)

    # Synthesize path can leave example empty — fine
    path.write_text(text, encoding="utf-8")
    print("OK orchestrator localize example")


def patch_frontend_types() -> None:
    path = ROOT / "frontend/types/lesson.ts"
    replace_once(
        path,
        "  diagram_steps?: { title: string; detail?: string }[];\n",
        "  diagram_steps?: { title: string; detail?: string; example?: string }[];\n",
        "diagram_steps example type",
    )


def patch_reel_stage() -> None:
    path = ROOT / "frontend/components/player/ReelStage.tsx"
    replace_once(
        path,
        "      .map((s) => ({ title: String(s.title || \"\").trim(), detail: String(s.detail || \"\").trim() }))\n",
        "      .map((s) => ({\n"
        "        title: String(s.title || \"\").trim(),\n"
        "        detail: String(s.detail || \"\").trim(),\n"
        "        example: String(s.example || \"\").trim(),\n"
        "      }))\n",
        "ReelStage pass example",
    )
    # bullets fallback should include empty example
    replace_once(
        path,
        '    return (scene.bullets || []).map((b) => ({ title: String(b || "").trim(), detail: "" })).filter((s) => s.title);\n',
        '    return (scene.bullets || []).map((b) => ({ title: String(b || "").trim(), detail: "", example: "" })).filter((s) => s.title);\n',
        "ReelStage bullets fallback example",
    )


def patch_export() -> None:
    path = ROOT / "frontend/lib/reelExport.ts"
    text = path.read_text(encoding="utf-8")
    old_steps = (
        "  const steps = (scene.diagram_steps || [])\n"
        "    .map((s) => ({ title: String(s.title || \"\").trim(), detail: String(s.detail || \"\").trim() }))\n"
        "    .filter((s) => s.title);\n"
    )
    new_steps = (
        "  const steps = (scene.diagram_steps || [])\n"
        "    .map((s) => ({\n"
        "      title: String(s.title || \"\").trim(),\n"
        "      detail: String(s.detail || \"\").trim(),\n"
        "      example: String((s as { example?: string }).example || \"\").trim(),\n"
        "    }))\n"
        "    .filter((s) => s.title);\n"
    )
    if "example: String((s as { example?: string }).example" in text:
        print("SKIP export steps map already has example")
    else:
        if old_steps not in text:
            raise SystemExit("export steps map missing")
        text = text.replace(old_steps, new_steps, 1)

    # Replace the entire explainer drawing block (from `if (explainer) {` with stacked cards
    # through `return;` before Info mode)
    marker_start = "  if (explainer) {\n    const count = bullets.length;"
    marker_end = "    return;\n  }\n\n  // Info mode — violet bullets (unchanged look)"
    i0 = text.find(marker_start)
    i1 = text.find(marker_end)
    if i0 < 0 or i1 < 0:
        if "explainer-mini dots" in text or "ONE big active card" in text or "mini pipeline dots" in text:
            print("SKIP export explainer panel already focus-stage")
        else:
            raise SystemExit("export explainer block markers missing")
    else:
        new_block = '''  if (explainer) {
    // Focus-stage export: mini pipeline dots + ONE big active card (not stacked list)
    const count = bullets.length;
    const ai = Math.max(0, Math.min(anim.active, Math.max(0, count - 1)));
    const examples = steps.length ? steps.map((s) => s.example || "") : bullets.map(() => "");
    const padX = pad;
    const miniY = y + 6;
    const miniR = 9;
    const trackLeft = x + padX + 18;
    const trackRight = x + w - padX - 18;
    const trackW = Math.max(40, trackRight - trackLeft);

    // Track
    ctx.save();
    ctx.strokeStyle = "rgba(34,211,238,0.16)";
    ctx.lineWidth = 3;
    ctx.lineCap = "round";
    ctx.beginPath();
    ctx.moveTo(trackLeft, miniY);
    ctx.lineTo(trackRight, miniY);
    ctx.stroke();
    const drawFrac = count <= 1 ? 1 : ai / Math.max(1, count - 1);
    ctx.strokeStyle = "rgba(34,211,238,0.65)";
    ctx.shadowColor = "rgba(34,211,238,0.4)";
    ctx.shadowBlur = 8;
    ctx.beginPath();
    ctx.moveTo(trackLeft, miniY);
    ctx.lineTo(trackLeft + trackW * drawFrac, miniY);
    ctx.stroke();
    ctx.restore();

    for (let index = 0; index < count; index++) {
      const visible = index < anim.visibleCount;
      const active = index === ai && visible;
      const past = visible && index < ai;
      const cx = count <= 1 ? (trackLeft + trackRight) / 2 : trackLeft + (trackW * index) / Math.max(1, count - 1);
      ctx.beginPath();
      ctx.arc(cx, miniY, miniR, 0, Math.PI * 2);
      if (active) {
        ctx.fillStyle = "#fbbf24";
        ctx.shadowColor = "rgba(251,191,36,0.55)";
        ctx.shadowBlur = 12;
      } else if (past) {
        ctx.fillStyle = "rgba(34,211,238,0.85)";
        ctx.shadowBlur = 0;
      } else {
        ctx.fillStyle = "rgba(255,255,255,0.12)";
        ctx.shadowBlur = 0;
      }
      ctx.fill();
      ctx.shadowBlur = 0;
      ctx.fillStyle = active ? "#09090b" : past ? "#083344" : "rgba(207,250,254,0.35)";
      ctx.font = "800 10px ui-sans-serif, system-ui";
      ctx.textAlign = "center";
      ctx.fillText(String(index + 1), cx, miniY + 3);
    }

    // Traveling token
    if (anim.visibleCount > 0) {
      const tx = count <= 1 ? (trackLeft + trackRight) / 2 : trackLeft + trackW * drawFrac;
      const pulse = 0.85 + 0.15 * Math.sin(elapsed * 6);
      ctx.save();
      ctx.beginPath();
      ctx.arc(tx, miniY, 6 * pulse, 0, Math.PI * 2);
      const tg = ctx.createRadialGradient(tx - 2, miniY - 2, 1, tx, miniY, 8);
      tg.addColorStop(0, "#fff7ed");
      tg.addColorStop(0.4, "#fbbf24");
      tg.addColorStop(1, "#22d3ee");
      ctx.fillStyle = tg;
      ctx.shadowColor = "rgba(34,211,238,0.9)";
      ctx.shadowBlur = 14;
      ctx.fill();
      ctx.restore();
    }

    // ONE big active card
    const cardTop = miniY + 28;
    const cardH = Math.max(160, panelTop + panelH - pad - cardTop);
    const cardX = x + padX;
    const cardW = w - padX * 2;
    const local = Math.max(0, Math.min(1, (elapsed - (anim.beats[ai]?.start ?? 0)) / 0.35));
    const ease = 1 - Math.pow(1 - local, 3);

    ctx.save();
    ctx.globalAlpha = 0.45 + 0.55 * ease;
    ctx.translate(0, (1 - ease) * 16);
    roundRect(ctx, cardX, cardTop, cardW, cardH, 18);
    ctx.fillStyle = "rgba(8,51,68,0.88)";
    ctx.fill();
    ctx.strokeStyle = "rgba(103,232,249,0.7)";
    ctx.lineWidth = 1.8;
    ctx.shadowColor = "rgba(34,211,238,0.4)";
    ctx.shadowBlur = 18;
    ctx.stroke();
    ctx.shadowBlur = 0;

    ctx.textAlign = "left";
    ctx.fillStyle = "rgba(253,230,138,0.95)";
    ctx.font = "800 12px ui-sans-serif, system-ui";
    ctx.fillText(`STEP ${ai + 1} OF ${count}`, cardX + 18, cardTop + 28);

    ctx.fillStyle = "#ffffff";
    ctx.font = "800 22px ui-sans-serif, system-ui";
    wrapLines(ctx, bullets[ai] || "", cardW - 36, 2).forEach((line, li) => {
      ctx.fillText(line, cardX + 18, cardTop + 58 + li * 26);
    });

    if (details[ai]) {
      ctx.fillStyle = "rgba(165,243,252,0.92)";
      ctx.font = "500 15px ui-sans-serif, system-ui";
      wrapLines(ctx, details[ai], cardW - 36, 3).forEach((line, li) => {
        ctx.fillText(line, cardX + 18, cardTop + 112 + li * 20);
      });
    }

    const ex = examples[ai] || "";
    if (ex) {
      const boxY = cardTop + cardH - 78;
      roundRect(ctx, cardX + 14, boxY, cardW - 28, 58, 12);
      ctx.fillStyle = "rgba(0,0,0,0.45)";
      ctx.fill();
      ctx.strokeStyle = "rgba(34,211,238,0.28)";
      ctx.lineWidth = 1;
      ctx.stroke();
      ctx.fillStyle = "rgba(103,232,249,0.75)";
      ctx.font = "700 11px ui-sans-serif, system-ui";
      ctx.fillText("EXAMPLE", cardX + 26, boxY + 18);
      ctx.fillStyle = "rgba(254,243,199,0.95)";
      ctx.font = "600 14px ui-monospace, SFMono-Regular, Menlo, monospace";
      wrapLines(ctx, ex, cardW - 56, 2).forEach((line, li) => {
        ctx.fillText(line, cardX + 26, boxY + 38 + li * 16);
      });
    }
    ctx.restore();
    return;
  }

  // Info mode — violet bullets (unchanged look)'''
        text = text[:i0] + new_block + text[i1 + len(marker_end) :]
        # Wait - I included marker_end content in new_block, so I should cut from i0 to i1+len(marker_end)
        # Actually I built new_block ending with the Info mode comment, and then did text[i1+len(marker_end):]
        # which drops the Info mode comment from the original. Good since new_block has it.

    path.write_text(text, encoding="utf-8")
    print("OK reelExport focus-stage panel")


def patch_css() -> None:
    path = ROOT / "frontend/app/globals.css"
    text = path.read_text(encoding="utf-8")
    if ".explainer-stage-card" in text:
        print("SKIP css: stage card already")
        return
    addition = '''

/* Focus-stage Explainer (one active card + mini pipeline) */
.explainer-mini-node.is-active {
  animation: explainer-mini-pulse 1.15s ease-in-out infinite;
}

@keyframes explainer-mini-pulse {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.12);
  }
}

.explainer-stage-card {
  animation: explainer-stage-enter 0.45s cubic-bezier(0.22, 1, 0.36, 1);
}

@keyframes explainer-stage-enter {
  0% {
    opacity: 0;
    transform: translateY(14px) scale(0.97);
  }
  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.explainer-example-chip {
  animation: explainer-example-pop 0.4s cubic-bezier(0.22, 1, 0.36, 1) 0.08s both;
}

@keyframes explainer-example-pop {
  0% {
    opacity: 0;
    transform: translateY(8px) scale(0.96);
  }
  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}
'''
    path.write_text(text.rstrip() + "\n" + addition, encoding="utf-8")
    print("OK globals.css focus-stage animations")


def patch_lesson_db() -> None:
    db = ROOT / "backend/tutor.db"
    lesson_id = "les_15a76019f0b847138917f91bd50819da"
    examples = [
        "Student s = new Student();",
        "s → heap object (active ref)",
        "s = null; // no one points to it",
        "GC marks unreachable objects",
        "heap memory freed (sweep)",
    ]
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("SELECT lesson_json FROM lessons WHERE id = ?", (lesson_id,))
    row = cur.fetchone()
    if not row:
        raise SystemExit(f"lesson {lesson_id} not in {db}")
    data = json.loads(row[0]) if isinstance(row[0], str) else row[0]
    patched = False
    for scene in data.get("scenes") or []:
        if scene.get("type") != "concept":
            continue
        steps = scene.get("diagram_steps") or []
        if not steps:
            continue
        for i, step in enumerate(steps):
            ex = examples[i] if i < len(examples) else ""
            if not step.get("example"):
                step["example"] = ex
                patched = True
            else:
                # refresh to the intended Hindi-friendly micro examples
                step["example"] = ex
                patched = True
        scene["diagram_steps"] = steps
    if not patched:
        raise SystemExit("no diagram_steps to patch")
    cur.execute(
        "UPDATE lessons SET lesson_json = ?, updated_at = datetime('now') WHERE id = ?",
        (json.dumps(data, ensure_ascii=False), lesson_id),
    )
    conn.commit()
    # verify
    cur.execute("SELECT lesson_json FROM lessons WHERE id = ?", (lesson_id,))
    verify = json.loads(cur.fetchone()[0])
    concept = next(s for s in verify["scenes"] if s["type"] == "concept")
    for s in concept["diagram_steps"]:
        assert s.get("example"), s
        print("  example:", s["title"][:40], "→", s["example"])
    conn.close()
    print("OK patched lesson DB", lesson_id)


def patch_verify_script() -> None:
    path = ROOT / "scripts/verify_explainer_focus_example.py"
    path.write_text(
        '''#!/usr/bin/env python3
import importlib.util
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder")
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.schemas.lesson import DiagramStep, ConceptScene

step = DiagramStep(title="create", detail="alloc", example="Student s = new Student();")
assert step.example.startswith("Student")
scene = ConceptScene(id="c1", duration=14, narration="GC", diagram_steps=[step], bullets=["create"])
assert scene.diagram_steps[0].example

spec = importlib.util.spec_from_file_location("topic_mode_direct", BACKEND / "app/agents/topic_mode.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
instr = mod.explainer_reel_planner_instruction(30)
assert "example" in instr.lower()
assert "micro" in instr.lower() or "tiny" in instr.lower()
assert "Main.java" in instr  # still bans full programs
assert "REQUIRED" in instr or "required" in instr.lower() or "MUST" in instr

flow = (ROOT / "frontend/components/player/ExplainerFlow.tsx").read_text(encoding="utf-8")
assert "explainer-stage-card" in flow
assert "explainer-mini-pipeline" in flow
assert "explainer-example-chip" in flow
assert "<ul" not in flow or flow.count("<ul") == 0  # no stacked card list
assert "Step {" in flow or "Step $" in flow or "Step {safeActive" in flow

types = (ROOT / "frontend/types/lesson.ts").read_text(encoding="utf-8")
assert "example?: string" in types

stage = (ROOT / "frontend/components/player/ReelStage.tsx").read_text(encoding="utf-8")
assert "example: String(s.example" in stage

export = (ROOT / "frontend/lib/reelExport.ts").read_text(encoding="utf-8")
assert "ONE big active card" in export or "Focus-stage export" in export
assert "EXAMPLE" in export
# Info mode still present
assert "Info mode — violet bullets" in export

orch = (BACKEND / "app/agents/orchestrator.py").read_text(encoding="utf-8")
assert "raw_example" in orch
assert "texts.append(str(example))" in orch

conn = sqlite3.connect(BACKEND / "tutor.db")
cur = conn.cursor()
cur.execute("SELECT lesson_json FROM lessons WHERE id = ?", ("les_15a76019f0b847138917f91bd50819da",))
row = cur.fetchone()
assert row, "lesson missing"
data = json.loads(row[0])
concept = next(s for s in data["scenes"] if s["type"] == "concept")
assert all(s.get("example") for s in concept["diagram_steps"]), concept["diagram_steps"]
assert "new Student" in concept["diagram_steps"][0]["example"]
assert "null" in concept["diagram_steps"][2]["example"]
conn.close()
print("verify_explainer_focus_example OK")
''',
        encoding="utf-8",
    )
    print("OK wrote verify script")


def main() -> None:
    write_explainer_flow()
    patch_schema()
    patch_planner()
    patch_orchestrator()
    patch_frontend_types()
    patch_reel_stage()
    patch_export()
    patch_css()
    patch_lesson_db()
    patch_verify_script()
    print("ALL DONE")


if __name__ == "__main__":
    main()
