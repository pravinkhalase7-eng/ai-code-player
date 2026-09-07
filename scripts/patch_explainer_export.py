#!/usr/bin/env python3
"""Update reelExport drawConceptPanel for explainer diagrams."""
from pathlib import Path

ROOT = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder")
path = ROOT / "frontend/lib/reelExport.ts"
text = path.read_text(encoding="utf-8")

old_blip = '''function scheduleConceptBlips(audioCtx: AudioContext, dest: MediaStreamAudioDestinationNode, scene: LessonScene, duration: number) {
  if (scene.type !== "concept") return;
  const beats = infoBulletAt(scene.bullets || [], 0, duration).beats;'''

new_blip = '''function scheduleConceptBlips(audioCtx: AudioContext, dest: MediaStreamAudioDestinationNode, scene: LessonScene, duration: number) {
  if (scene.type !== "concept") return;
  const titles =
    (scene.diagram_steps || []).map((s) => String(s.title || "").trim()).filter(Boolean).length
      ? (scene.diagram_steps || []).map((s) => String(s.title || "").trim()).filter(Boolean)
      : scene.bullets || [];
  const beats = infoBulletAt(titles, 0, duration).beats;'''

if old_blip not in text:
    raise SystemExit("scheduleConceptBlips missing")
text = text.replace(old_blip, new_blip, 1)

old_draw = '''function drawConceptPanel(
  ctx: CanvasRenderingContext2D,
  scene: LessonScene,
  elapsed: number,
  duration: number,
  topic: string,
) {
  const footer = 220;
  const headerBottom = 188;
  const available = HEIGHT - footer - headerBottom;
  const panelH = Math.min(available, 520);
  const panelTop = headerBottom + Math.max(0, (available - panelH) / 2);
  const x = 28;
  const w = WIDTH - 108;

  const t = elapsed;
  const orbs = [
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
  ctx.fillStyle = "rgba(196,181,253,0.95)";
  ctx.font = "700 16px ui-sans-serif, system-ui";
  ctx.fillText("EXPLAIN", WIDTH / 2, 88);
  ctx.fillStyle = "#ffffff";
  ctx.font = "700 28px ui-sans-serif, system-ui";
  wrapLines(ctx, topic, WIDTH - 120, 2).forEach((line, index) => {
    ctx.fillText(line, WIDTH / 2, 126 + index * 34);
  });
  ctx.textAlign = "left";

  roundRect(ctx, x, panelTop, w, panelH, 22);
  ctx.fillStyle = "rgba(18,7,31,0.92)";
  ctx.fill();
  ctx.strokeStyle = "rgba(196,181,253,0.22)";
  ctx.lineWidth = 1.5;
  ctx.stroke();

  const bullets = (scene.bullets || []).map((b) => String(b || "").trim()).filter(Boolean);
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
    wrapLines(ctx, item, w - pad * 2 - 56, 2).forEach((line, li) => {
      ctx.fillText(line, x + pad + 44, by + 28 + li * 22);
    });
    ctx.restore();
  });
}'''

new_draw = '''function drawConceptPanel(
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
  ctx.fillStyle = explainer ? "rgba(4,21,28,0.92)" : "rgba(18,7,31,0.92)";
  ctx.fill();
  ctx.strokeStyle = explainer ? "rgba(34,211,238,0.28)" : "rgba(196,181,253,0.22)";
  ctx.lineWidth = 1.5;
  ctx.stroke();

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

  const slot = Math.min(explainer ? 92 : 86, Math.max(58, (panelH - pad * 2) / Math.max(1, bullets.length)));
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
    ctx.fillStyle = active
      ? explainer
        ? "rgba(8,51,68,0.72)"
        : "rgba(91,33,182,0.45)"
      : "rgba(0,0,0,0.35)";
    ctx.fill();
    ctx.strokeStyle = active
      ? explainer
        ? "rgba(103,232,249,0.6)"
        : "rgba(196,181,253,0.55)"
      : "rgba(255,255,255,0.12)";
    ctx.lineWidth = 1.2;
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(x + pad + 22, by + (slot - 12) / 2, 12, 0, Math.PI * 2);
    ctx.fillStyle = explainer ? "rgba(34,211,238,0.3)" : "rgba(167,139,250,0.3)";
    ctx.fill();
    ctx.fillStyle = explainer ? "#cffafe" : "#ede9fe";
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
      ctx.fillStyle = "rgba(165,243,252,0.75)";
      ctx.font = "500 13px ui-sans-serif, system-ui";
      wrapLines(ctx, details[index], w - pad * 2 - 56, 1).forEach((line, li) => {
        ctx.fillText(line, x + pad + 44, by + 46 + li * 16);
      });
    }
    ctx.restore();
  });
}'''

if old_draw not in text:
    raise SystemExit("drawConceptPanel missing")
text = text.replace(old_draw, new_draw, 1)

# Update call site
text = text.replace(
    "  } else if (scene.type === \"concept\" || lesson.requires_code === false) {\n"
    "    drawConceptPanel(ctx, scene, elapsed, duration, topic);\n"
    "  } else {",
    "  } else if (scene.type === \"concept\" || lesson.requires_code === false || lesson.reel_mode === \"explainer\") {\n"
    "    drawConceptPanel(ctx, scene, elapsed, duration, topic, lesson);\n"
    "  } else {",
    1,
)

path.write_text(text, encoding="utf-8")
print("reelExport ok")
