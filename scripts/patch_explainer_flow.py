#!/usr/bin/env python3
"""Upgrade Explainer UI: motion-graphics flow diagram (ExplainerFlow + CSS + export)."""
from pathlib import Path

ROOT = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder")
FE = ROOT / "frontend"

EXPLAINER_FLOW = r'''"use client";

import { useMemo } from "react";
import {
  AppWindow,
  Binary,
  Box,
  Braces,
  ChevronDown,
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

export type ExplainerFlowStep = { title: string; detail: string };

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
  if (/\b(factory|builder|create|construct)\b/.test(t)) return Factory;
  if (/\b(call|invoke|dispatch|phone)\b/.test(t)) return PhoneCall;
  if (/\b(hash|digest|checksum)\b/.test(t)) return Hash;
  if (/\b(bucket|map|dict|table|store|db|database)\b/.test(t)) return Database;
  if (/\b(key|lookup|index)\b/.test(t)) return Key;
  if (/\b(value|payload|data|object)\b/.test(t)) return Box;
  if (/\b(memory|heap|stack|ram|cache)\b/.test(t)) return MemoryStick;
  if (/\b(package|module|import)\b/.test(t)) return Package;
  if (/\b(cpu|runtime|vm|process)\b/.test(t)) return Cpu;
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

  const icons = useMemo(
    () => steps.map((s) => pickIcon(s.title, s.detail, topic)),
    [steps, topic],
  );

  const spineH = Math.max(120, n * 88);
  const drawLen = Math.max(40, (Math.min(visibleCount, n) / n) * spineH);

  return (
    <div className="explainer-flow relative flex min-h-0 flex-1 flex-col overflow-hidden rounded-2xl border border-cyan-200/25 bg-[#031018]/94 p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]">
      <div className="explainer-flow-grid pointer-events-none absolute inset-0" aria-hidden />
      <div className="explainer-flow-lanes pointer-events-none absolute inset-y-3 left-1/2 w-px -translate-x-1/2" aria-hidden />

      <div className="relative z-10 flex min-h-0 flex-1 flex-col justify-center">
        <div className="relative mx-auto w-full max-w-[22rem]">
          {/* Vertical spine + traveling token */}
          <div
            className="pointer-events-none absolute left-[1.35rem] top-3 bottom-3 w-8"
            aria-hidden
          >
            <svg
              className="explainer-spine-svg absolute left-1/2 top-0 h-full w-6 -translate-x-1/2"
              viewBox={`0 0 24 ${spineH}`}
              preserveAspectRatio="none"
            >
              <defs>
                <linearGradient id="explainerSpineGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="rgba(34,211,238,0.15)" />
                  <stop offset="50%" stopColor="rgba(251,191,36,0.7)" />
                  <stop offset="100%" stopColor="rgba(34,211,238,0.2)" />
                </linearGradient>
                <filter id="explainerSpineGlow" x="-50%" y="-10%" width="200%" height="120%">
                  <feGaussianBlur stdDeviation="1.6" result="b" />
                  <feMerge>
                    <feMergeNode in="b" />
                    <feMergeNode in="SourceGraphic" />
                  </feMerge>
                </filter>
              </defs>
              <line
                x1="12"
                y1="0"
                x2="12"
                y2={spineH}
                stroke="rgba(34,211,238,0.12)"
                strokeWidth="3"
                strokeLinecap="round"
              />
              <line
                className="explainer-spine-draw"
                x1="12"
                y1="0"
                x2="12"
                y2={spineH}
                stroke="url(#explainerSpineGrad)"
                strokeWidth="3"
                strokeLinecap="round"
                filter="url(#explainerSpineGlow)"
                strokeDasharray={spineH}
                strokeDashoffset={Math.max(0, spineH - drawLen)}
              />
            </svg>
            <div
              className="explainer-token absolute left-1/2 z-20"
              style={{ top: `calc(${tokenPct}% )`, transform: "translate(-50%, -50%)" }}
            >
              <span className="explainer-token-orb" />
            </div>
          </div>

          <ul className="relative z-10 flex flex-col gap-2.5 pl-0">
            {steps.map((step, index) => {
              const Icon = icons[index] || Hexagon;
              const visible = visibleCount > index;
              const isActive = active === index && visible;
              const isPast = visible && index < active;
              const isFuture = !visible;
              return (
                <li
                  key={`${index}-${step.title}`}
                  className={cn(
                    "explainer-flow-node relative flex items-stretch gap-2.5 rounded-xl border px-2.5 py-2.5 backdrop-blur-md transition-all duration-400",
                    "border-white/10 bg-black/40",
                    visible && "is-visible",
                    isActive && "is-active",
                    isPast && "is-past",
                    isFuture && "is-future",
                  )}
                  style={{ transitionDelay: visible ? `${Math.min(index, 5) * 40}ms` : "0ms" }}
                >
                  <div className="relative flex shrink-0 flex-col items-center pt-0.5">
                    <span
                      className={cn(
                        "explainer-step-badge inline-flex h-7 w-7 items-center justify-center rounded-full text-[11px] font-extrabold",
                        isActive
                          ? "bg-amber-400 text-zinc-950 shadow-[0_0_18px_rgba(251,191,36,0.55)]"
                          : "bg-cyan-400/25 text-cyan-100",
                      )}
                    >
                      {index + 1}
                    </span>
                    {index < steps.length - 1 ? (
                      <span className={cn("explainer-chevron mt-1", visible && "is-visible")} aria-hidden>
                        <ChevronDown className="h-3.5 w-3.5 text-cyan-300/70" strokeWidth={2.5} />
                      </span>
                    ) : null}
                  </div>

                  <div
                    className={cn(
                      "explainer-node-icon mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border",
                      isActive
                        ? "border-cyan-300/50 bg-cyan-400/20 text-cyan-100"
                        : "border-white/10 bg-white/5 text-cyan-200/70",
                    )}
                  >
                    <Icon className="h-4 w-4" strokeWidth={2.25} />
                  </div>

                  <div className="min-w-0 flex-1">
                    <p
                      className={cn(
                        "text-[13px] font-bold leading-4 tracking-tight",
                        isActive ? "text-white" : "text-zinc-100",
                      )}
                    >
                      {step.title}
                    </p>
                    {step.detail ? (
                      <p
                        className={cn(
                          "mt-1 text-[11px] font-medium leading-4",
                          isActive ? "text-cyan-100/90" : "text-cyan-100/55",
                          !isActive && "line-clamp-2",
                        )}
                      >
                        {step.detail}
                      </p>
                    ) : null}
                  </div>

                  {isActive ? <span className="explainer-glow-ring pointer-events-none absolute inset-0 rounded-xl" /> : null}
                </li>
              );
            })}
          </ul>
        </div>
      </div>
    </div>
  );
}
'''

def patch_reel_stage():
    path = FE / "components/player/ReelStage.tsx"
    text = path.read_text(encoding="utf-8")
    if "ExplainerFlow" not in text:
        text = text.replace(
            'import { ReelCodePanel } from "@/components/player/ReelCodePanel";\n',
            'import { ReelCodePanel } from "@/components/player/ReelCodePanel";\n'
            'import { ExplainerFlow } from "@/components/player/ExplainerFlow";\n',
            1,
        )
    old = '''              {isExplainer && diagramSteps.length ? (
                diagramSteps.map((item, index) => {
                  const visible = (infoAnim?.visibleCount ?? 0) > index;
                  const active = infoAnim?.active === index;
                  return (
                    <div key={`${index}-${item.title}`}>
                      {index > 0 ? (
                        <div className={cn("explainer-connector", visible && "is-visible")} />
                      ) : null}
                      <div
                        className={cn(
                          "explainer-node rounded-xl border border-white/10 bg-black/35 px-3 py-2",
                          visible && "is-visible",
                          active && "is-active",
                        )}
                      >
                        <p className="flex items-start gap-2 text-sm font-semibold leading-5 text-zinc-50">
                          <span className="mt-0.5 inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-cyan-400/25 px-1.5 text-[10px] font-bold text-cyan-100">
                            {index + 1}
                          </span>
                          <span className="min-w-0 flex-1">
                            {item.title}
                            {item.detail ? (
                              <span className="mt-0.5 block text-xs font-medium leading-4 text-cyan-100/75">
                                {item.detail}
                              </span>
                            ) : null}
                          </span>
                        </p>
                      </div>
                    </div>
                  );
                })
              ) : (scene.bullets || []).length ? ('''
    new = '''              {isExplainer && diagramSteps.length ? (
                <ExplainerFlow
                  steps={diagramSteps}
                  active={infoAnim?.active ?? 0}
                  visibleCount={infoAnim?.visibleCount ?? 0}
                  topic={topic}
                />
              ) : (scene.bullets || []).length ? ('''
    if old not in text:
        if "ExplainerFlow" in text and "<ExplainerFlow" in text:
            print("ReelStage already wired")
        else:
            raise SystemExit("ReelStage explainer block not found")
    else:
        text = text.replace(old, new, 1)
        # Concept panel wrapper: for ExplainerFlow, drop nested scroll card chrome
        # Keep outer shell but ExplainerFlow has its own glass panel — simplify outer when explainer
        old_wrap_open = '''          <div className="relative z-10 flex min-h-0 flex-1 flex-col items-stretch justify-center py-2">
            <div
              className={cn(
                "flex max-h-full min-h-0 flex-col gap-2 overflow-y-auto rounded-2xl border p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]",
                isExplainer
                  ? "border-cyan-200/20 bg-[#04151c]/92"
                  : "border-violet-200/20 bg-[#12071f]/92",
              )}
            >
              {isExplainer && diagramSteps.length ? (
                <ExplainerFlow
                  steps={diagramSteps}
                  active={infoAnim?.active ?? 0}
                  visibleCount={infoAnim?.visibleCount ?? 0}
                  topic={topic}
                />
              ) : (scene.bullets || []).length ? ('''
        new_wrap_open = '''          <div className="relative z-10 flex min-h-0 flex-1 flex-col items-stretch justify-center py-2">
            {isExplainer && diagramSteps.length ? (
              <ExplainerFlow
                steps={diagramSteps}
                active={infoAnim?.active ?? 0}
                visibleCount={infoAnim?.visibleCount ?? 0}
                topic={topic}
              />
            ) : (
            <div
              className={cn(
                "flex max-h-full min-h-0 flex-col gap-2 overflow-y-auto rounded-2xl border p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]",
                "border-violet-200/20 bg-[#12071f]/92",
              )}
            >
              {(scene.bullets || []).length ? ('''
        if old_wrap_open in text:
            text = text.replace(old_wrap_open, new_wrap_open, 1)
            # close the extra paren/div after the info bullets / narration branch
            old_close = '''              ) : (
                <p className="text-sm leading-6 text-zinc-200">{narration}</p>
              )}
            </div>
          </div>
        </>
      ) : ('''
            new_close = '''              ) : (
                <p className="text-sm leading-6 text-zinc-200">{narration}</p>
              )}
            </div>
            )}
          </div>
        </>
      ) : ('''
            if old_close not in text:
                raise SystemExit("ReelStage close block not found after wrap change")
            text = text.replace(old_close, new_close, 1)
        path.write_text(text, encoding="utf-8")
        print("ReelStage ok")


def patch_globals():
    path = FE / "app/globals.css"
    text = path.read_text(encoding="utf-8")
    # Remove old explainer-node / connector styles; keep info-bullet
    start = text.find("\n.explainer-node {")
    if start == -1:
        start = text.find(".explainer-node {")
    if start != -1:
        text = text[:start].rstrip() + "\n"
    new_css = r'''
/* --- Explainer motion-graphics flow --- */
.explainer-flow-grid {
  background-image:
    linear-gradient(rgba(34, 211, 238, 0.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(34, 211, 238, 0.05) 1px, transparent 1px);
  background-size: 28px 28px;
  mask-image: radial-gradient(ellipse 75% 70% at 50% 45%, #000 35%, transparent 85%);
  opacity: 0.9;
}

.explainer-flow-lanes {
  background: repeating-linear-gradient(
    180deg,
    transparent 0 10px,
    rgba(34, 211, 238, 0.14) 10px 12px
  );
  opacity: 0.35;
  filter: blur(0.2px);
}

.explainer-spine-draw {
  transition: stroke-dashoffset 0.55s cubic-bezier(0.22, 1, 0.36, 1);
}

.explainer-token {
  transition: top 0.55s cubic-bezier(0.22, 1, 0.36, 1);
  will-change: top;
}

.explainer-token-orb {
  display: block;
  width: 14px;
  height: 14px;
  border-radius: 9999px;
  background: radial-gradient(circle at 30% 30%, #fff7ed 0%, #fbbf24 35%, #22d3ee 100%);
  box-shadow:
    0 0 0 2px rgba(8, 51, 68, 0.85),
    0 0 16px rgba(34, 211, 238, 0.85),
    0 0 28px rgba(251, 191, 36, 0.45);
  animation: explainer-token-pulse 1.1s ease-in-out infinite;
}

@keyframes explainer-token-pulse {
  0%,
  100% {
    transform: scale(1);
    filter: brightness(1);
  }
  50% {
    transform: scale(1.18);
    filter: brightness(1.15);
  }
}

.explainer-flow-node {
  opacity: 0;
  transform: translateY(18px) scale(0.94);
  filter: blur(5px);
  transition:
    opacity 0.4s ease,
    transform 0.45s cubic-bezier(0.22, 1, 0.36, 1),
    filter 0.35s ease,
    border-color 0.25s ease,
    background 0.25s ease,
    box-shadow 0.25s ease;
}

.explainer-flow-node.is-visible {
  opacity: 0.72;
  transform: translateY(0) scale(1);
  filter: blur(0);
}

.explainer-flow-node.is-past {
  opacity: 0.55;
  border-color: rgba(34, 211, 238, 0.18);
  background: rgba(0, 0, 0, 0.28);
}

.explainer-flow-node.is-future {
  opacity: 0.18;
  transform: translateY(10px) scale(0.97);
  filter: blur(1.5px);
}

.explainer-flow-node.is-active {
  opacity: 1 !important;
  transform: translateY(0) scale(1.035) !important;
  filter: blur(0) !important;
  border-color: rgba(103, 232, 249, 0.65) !important;
  background: rgba(8, 51, 68, 0.78) !important;
  box-shadow:
    0 0 0 1px rgba(34, 211, 238, 0.35),
    0 12px 36px rgba(8, 145, 178, 0.4),
    0 0 40px rgba(34, 211, 238, 0.18);
  animation: explainer-node-enter 0.5s cubic-bezier(0.22, 1, 0.36, 1);
}

@keyframes explainer-node-enter {
  0% {
    transform: translateY(10px) scale(0.96);
  }
  65% {
    transform: translateY(-2px) scale(1.05);
  }
  100% {
    transform: translateY(0) scale(1.035);
  }
}

.explainer-glow-ring {
  box-shadow: inset 0 0 0 1px rgba(103, 232, 249, 0.35);
  animation: explainer-glow 1.6s ease-in-out infinite;
  pointer-events: none;
}

@keyframes explainer-glow {
  0%,
  100% {
    opacity: 0.55;
    box-shadow:
      inset 0 0 0 1px rgba(103, 232, 249, 0.3),
      0 0 18px rgba(34, 211, 238, 0.25);
  }
  50% {
    opacity: 1;
    box-shadow:
      inset 0 0 0 1px rgba(251, 191, 36, 0.45),
      0 0 28px rgba(34, 211, 238, 0.45);
  }
}

.explainer-chevron {
  opacity: 0;
  transform: translateY(-4px);
  transition: opacity 0.35s ease, transform 0.35s ease;
}

.explainer-chevron.is-visible {
  opacity: 1;
  transform: translateY(0);
  animation: explainer-chevron-bob 1.4s ease-in-out infinite;
}

@keyframes explainer-chevron-bob {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(3px);
  }
}
'''
    text = text.rstrip() + "\n" + new_css
    path.write_text(text, encoding="utf-8")
    print("globals.css ok")


def patch_export():
    path = FE / "lib/reelExport.ts"
    text = path.read_text(encoding="utf-8")
    start = text.find("function drawConceptPanel(")
    if start < 0:
        raise SystemExit("drawConceptPanel not found")
    # Find next function after drawConceptPanel
    end = text.find("\nfunction drawFrame(", start)
    if end < 0:
        raise SystemExit("drawFrame after drawConceptPanel not found")

    replacement = r'''function drawConceptPanel(
  ctx: CanvasRenderingContext2D,
  scene: LessonScene,
  elapsed: number,
  duration: number,
  topic: string,
  lesson?: Lesson,
) {
  const footer = 220;
  const headerBottom = 188;
  const available = HEIGHT - footer - headerBottom;
  const panelH = Math.min(available, 520);
  const panelTop = headerBottom + Math.max(0, (available - panelH) / 2);
  const x = 28;
  const w = WIDTH - 108;
  const explainer =
    lesson?.reel_mode === "explainer" || Boolean(scene.diagram_steps && scene.diagram_steps.length);

  const t = elapsed;
  const orbs = explainer
    ? [
        { cx: 90, cy: panelTop + 40, r: 70, color: "rgba(34,211,238,0.28)", drift: 1 },
        { cx: WIDTH - 130, cy: panelTop + 160, r: 58, color: "rgba(251,191,36,0.22)", drift: 1.4 },
        { cx: 140, cy: panelTop + panelH - 40, r: 48, color: "rgba(45,212,191,0.18)", drift: 0.8 },
      ]
    : [
        { cx: 90, cy: panelTop + 40, r: 70, color: "rgba(139,92,246,0.28)", drift: 1 },
        { cx: WIDTH - 130, cy: panelTop + 160, r: 58, color: "rgba(232,121,249,0.22)", drift: 1.4 },
        { cx: 140, cy: panelTop + panelH - 40, r: 48, color: "rgba(34,211,238,0.18)", drift: 0.8 },
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
  ctx.fillStyle = explainer ? "rgba(103,232,249,0.95)" : "rgba(196,181,253,0.95)";
  ctx.font = "700 16px ui-sans-serif, system-ui";
  ctx.fillText(explainer ? "EXPLAINER" : "EXPLAIN", WIDTH / 2, 88);
  ctx.fillStyle = "#ffffff";
  ctx.font = "700 28px ui-sans-serif, system-ui";
  wrapLines(ctx, topic, WIDTH - 120, 2).forEach((line, index) => {
    ctx.fillText(line, WIDTH / 2, 126 + index * 34);
  });
  ctx.textAlign = "left";

  roundRect(ctx, x, panelTop, w, panelH, 22);
  ctx.fillStyle = explainer ? "rgba(3,16,24,0.94)" : "rgba(18,7,31,0.92)";
  ctx.fill();
  ctx.strokeStyle = explainer ? "rgba(34,211,238,0.28)" : "rgba(196,181,253,0.22)";
  ctx.lineWidth = 1.5;
  ctx.stroke();

  // Soft grid for explainer motion-graphic feel
  if (explainer) {
    ctx.save();
    ctx.beginPath();
    roundRect(ctx, x, panelTop, w, panelH, 22);
    ctx.clip();
    ctx.strokeStyle = "rgba(34,211,238,0.06)";
    ctx.lineWidth = 1;
    for (let gx = x + 8; gx < x + w; gx += 28) {
      ctx.beginPath();
      ctx.moveTo(gx, panelTop);
      ctx.lineTo(gx, panelTop + panelH);
      ctx.stroke();
    }
    for (let gy = panelTop + 8; gy < panelTop + panelH; gy += 28) {
      ctx.beginPath();
      ctx.moveTo(x, gy);
      ctx.lineTo(x + w, gy);
      ctx.stroke();
    }
    ctx.restore();
  }

  const steps = (scene.diagram_steps || [])
    .map((s) => ({ title: String(s.title || "").trim(), detail: String(s.detail || "").trim() }))
    .filter((s) => s.title);
  const bullets = steps.length
    ? steps.map((s) => s.title)
    : (scene.bullets || []).map((b) => String(b || "").trim()).filter(Boolean);
  const details = steps.length ? steps.map((s) => s.detail) : bullets.map(() => "");
  const anim = infoBulletAt(bullets, elapsed, duration);
  const pad = 22;
  let y = panelTop + pad + 8;
  if (!bullets.length) {
    ctx.fillStyle = "#e4e4e7";
    ctx.font = "600 18px ui-sans-serif, system-ui";
    wrapLines(ctx, stripDurationNoise(scene.narration || ""), w - pad * 2, 8).forEach((line, index) => {
      ctx.fillText(line, x + pad, y + index * 26);
    });
    return;
  }

  if (explainer) {
    const count = bullets.length;
    const slot = Math.min(96, Math.max(64, (panelH - pad * 2 - 8) / Math.max(1, count)));
    const nodeX = x + pad + 36;
    const nodeW = w - pad * 2 - 36;
    const spineX = x + pad + 14;
    const firstCy = y + (slot - 10) / 2;
    const lastCy = y + (count - 1) * slot + (slot - 10) / 2;
    const drawFrac = Math.min(1, Math.max(0.08, anim.visibleCount / Math.max(1, count)));

    // Spine track
    ctx.save();
    ctx.strokeStyle = "rgba(34,211,238,0.14)";
    ctx.lineWidth = 3;
    ctx.lineCap = "round";
    ctx.beginPath();
    ctx.moveTo(spineX, firstCy);
    ctx.lineTo(spineX, lastCy);
    ctx.stroke();
    ctx.strokeStyle = "rgba(34,211,238,0.55)";
    ctx.shadowColor = "rgba(34,211,238,0.45)";
    ctx.shadowBlur = 8;
    ctx.beginPath();
    ctx.moveTo(spineX, firstCy);
    ctx.lineTo(spineX, firstCy + (lastCy - firstCy) * drawFrac);
    ctx.stroke();
    ctx.restore();

    bullets.forEach((item, index) => {
      const visible = index < anim.visibleCount;
      const active = index === anim.active && visible;
      const by = y + index * slot;
      const cy = by + (slot - 10) / 2;
      const local = visible
        ? Math.max(0, Math.min(1, (elapsed - (anim.beats[index]?.start ?? 0)) / 0.35))
        : 0;
      const ease = 1 - Math.pow(1 - local, 3);

      // Connector chevron mid-path
      if (index < count - 1 && visible) {
        ctx.fillStyle = "rgba(103,232,249,0.55)";
        const midY = by + slot - 6;
        ctx.beginPath();
        ctx.moveTo(spineX - 5, midY - 4);
        ctx.lineTo(spineX + 5, midY - 4);
        ctx.lineTo(spineX, midY + 3);
        ctx.closePath();
        ctx.fill();
      }

      ctx.save();
      ctx.globalAlpha = visible ? 0.4 + 0.6 * ease : 0.12;
      if (!visible) ctx.globalAlpha = 0.14;
      else if (!active && index < anim.active) ctx.globalAlpha = 0.5;
      ctx.translate(0, visible ? (1 - ease) * 12 : 8);

      roundRect(ctx, nodeX, by, nodeW, slot - 10, 14);
      ctx.fillStyle = active ? "rgba(8,51,68,0.82)" : "rgba(0,0,0,0.38)";
      ctx.fill();
      ctx.strokeStyle = active ? "rgba(103,232,249,0.7)" : "rgba(255,255,255,0.12)";
      ctx.lineWidth = active ? 1.8 : 1.1;
      if (active) {
        ctx.shadowColor = "rgba(34,211,238,0.45)";
        ctx.shadowBlur = 16;
      }
      ctx.stroke();
      ctx.shadowBlur = 0;

      // Step badge
      ctx.beginPath();
      ctx.arc(spineX, cy, 11, 0, Math.PI * 2);
      ctx.fillStyle = active ? "#fbbf24" : "rgba(34,211,238,0.35)";
      ctx.fill();
      ctx.fillStyle = active ? "#09090b" : "#cffafe";
      ctx.font = "800 12px ui-sans-serif, system-ui";
      ctx.textAlign = "center";
      ctx.fillText(String(index + 1), spineX, cy + 4);

      // Mini geometric icon
      const ix = nodeX + 16;
      const iy = cy;
      ctx.strokeStyle = active ? "rgba(165,243,252,0.95)" : "rgba(165,243,252,0.45)";
      ctx.lineWidth = 1.6;
      ctx.beginPath();
      for (let k = 0; k < 6; k++) {
        const ang = (Math.PI / 3) * k - Math.PI / 6;
        const px = ix + Math.cos(ang) * 8;
        const py = iy + Math.sin(ang) * 8;
        if (k === 0) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      }
      ctx.closePath();
      ctx.stroke();

      ctx.textAlign = "left";
      ctx.fillStyle = "#f4f4f5";
      ctx.font = active ? "700 17px ui-sans-serif, system-ui" : "600 16px ui-sans-serif, system-ui";
      wrapLines(ctx, item, nodeW - 48, details[index] ? 1 : 2).forEach((line, li) => {
        ctx.fillText(line, nodeX + 32, by + 22 + li * 18);
      });
      if (details[index] && (active || visible)) {
        ctx.fillStyle = active ? "rgba(165,243,252,0.9)" : "rgba(165,243,252,0.55)";
        ctx.font = "500 13px ui-sans-serif, system-ui";
        wrapLines(ctx, details[index], nodeW - 48, active ? 2 : 1).forEach((line, li) => {
          ctx.fillText(line, nodeX + 32, by + 44 + li * 15);
        });
      }
      ctx.restore();
    });

    // Traveling token at active step
    if (anim.visibleCount > 0) {
      const ai = Math.max(0, Math.min(anim.active, count - 1));
      const ty = y + ai * slot + (slot - 10) / 2;
      const pulse = 0.85 + 0.15 * Math.sin(elapsed * 6);
      ctx.save();
      ctx.beginPath();
      ctx.arc(spineX, ty, 7 * pulse, 0, Math.PI * 2);
      const tg = ctx.createRadialGradient(spineX - 2, ty - 2, 1, spineX, ty, 9);
      tg.addColorStop(0, "#fff7ed");
      tg.addColorStop(0.4, "#fbbf24");
      tg.addColorStop(1, "#22d3ee");
      ctx.fillStyle = tg;
      ctx.shadowColor = "rgba(34,211,238,0.9)";
      ctx.shadowBlur = 14;
      ctx.fill();
      ctx.restore();
    }
    return;
  }

  // Info mode — violet bullets (unchanged look)
  const slot = Math.min(86, Math.max(58, (panelH - pad * 2) / Math.max(1, bullets.length)));
  bullets.forEach((item, index) => {
    if (index >= anim.visibleCount) return;
    const active = index === anim.active;
    const local = Math.max(0, Math.min(1, (elapsed - anim.beats[index].start) / 0.35));
    const ease = 1 - Math.pow(1 - local, 3);
    const by = y + index * slot;
    ctx.save();
    ctx.globalAlpha = 0.35 + 0.65 * ease;
    ctx.translate(0, (1 - ease) * 14);
    roundRect(ctx, x + pad, by, w - pad * 2, slot - 12, 14);
    ctx.fillStyle = active ? "rgba(91,33,182,0.45)" : "rgba(0,0,0,0.35)";
    ctx.fill();
    ctx.strokeStyle = active ? "rgba(196,181,253,0.55)" : "rgba(255,255,255,0.12)";
    ctx.lineWidth = 1.2;
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(x + pad + 22, by + (slot - 12) / 2, 12, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(167,139,250,0.3)";
    ctx.fill();
    ctx.fillStyle = "#ede9fe";
    ctx.font = "700 12px ui-sans-serif, system-ui";
    ctx.textAlign = "center";
    ctx.fillText(String(index + 1), x + pad + 22, by + (slot - 12) / 2 + 4);
    ctx.textAlign = "left";
    ctx.fillStyle = "#f4f4f5";
    ctx.font = "600 17px ui-sans-serif, system-ui";
    wrapLines(ctx, item, w - pad * 2 - 56, details[index] ? 1 : 2).forEach((line, li) => {
      ctx.fillText(line, x + pad + 44, by + 24 + li * 20);
    });
    if (details[index]) {
      ctx.fillStyle = "rgba(196,181,253,0.75)";
      ctx.font = "500 13px ui-sans-serif, system-ui";
      wrapLines(ctx, details[index], w - pad * 2 - 56, 1).forEach((line, li) => {
        ctx.fillText(line, x + pad + 44, by + 46 + li * 16);
      });
    }
    ctx.restore();
  });
}

'''
    text = text[:start] + replacement + text[end + 1 :]
    path.write_text(text, encoding="utf-8")
    print("reelExport ok")


def main():
    out = FE / "components/player/ExplainerFlow.tsx"
    out.write_text(EXPLAINER_FLOW, encoding="utf-8")
    print("wrote ExplainerFlow.tsx")
    patch_reel_stage()
    patch_globals()
    patch_export()
    print("ALL OK")


if __name__ == "__main__":
    main()
