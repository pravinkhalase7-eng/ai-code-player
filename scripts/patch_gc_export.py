from pathlib import Path

ROOT = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder")

# 1) Remove unused ExplainerFlow import from ReelStage
stage = ROOT / "frontend/components/player/ReelStage.tsx"
st = stage.read_text()
old_imp = 'import { ExplainerFlow } from "@/components/player/ExplainerFlow";\n'
rest = st.replace(old_imp, "", 1) if old_imp in st else st
if old_imp in st and "ExplainerFlow" not in rest:
    stage.write_text(rest)
    print("removed unused ExplainerFlow import")
else:
    print("ExplainerFlow refs:", st.count("ExplainerFlow"))

export = ROOT / "frontend/lib/reelExport.ts"
text = export.read_text()
if "function drawGcHeapBoard" in text:
    print("drawGcHeapBoard already exists")
else:
    helper = r'''
function isGcTopicExport(topic: string): boolean {
  const t = (topic || "").toLowerCase();
  return /garbage|garbege|\bgc\b|heap|mark\s*[- ]?\s*sweep|marking|sweep|compact|collector/.test(t);
}

function classifyGcPhaseExport(title: string, detail?: string, example?: string): string {
  const blob = `${title || ""} ${detail || ""} ${example || ""}`.toLowerCase();
  if (/compact|defrag|relocat/.test(blob)) return "compact";
  if (/sweep|reclaim|collect|free|delete|remove/.test(blob)) return "sweep";
  if (/mark|reachable|root|live/.test(blob)) return "mark";
  if (/unref|unreachable|dead|orphan|garbage|unused/.test(blob)) return "unref";
  if (/allocat|new\b|create|object|heap|store/.test(blob)) return "allocate";
  return "other";
}

/** Canvas twin of MechanismBoard GcHeapPanel for MP4 export. */
function drawGcHeapBoard(
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

  const steps = (scene.diagram_steps || [])
    .map((s) => ({
      title: String(s.title || "").trim(),
      detail: String(s.detail || "").trim(),
      example: String((s as { example?: string }).example || "").trim(),
    }))
    .filter((s) => s.title);
  const titles = steps.map((s) => s.title);
  const anim = infoBulletAt(titles.length ? titles : ["Heap"], elapsed, duration);
  const ai = Math.max(0, Math.min(anim.active, Math.max(0, Math.max(1, titles.length) - 1)));
  const step = steps[ai] || { title: topic, detail: "", example: "" };
  const phase = classifyGcPhaseExport(step.title, step.detail, step.example);
  const beat = anim.beats[ai];
  const local = Math.max(
    0,
    Math.min(1, (elapsed - (beat?.start ?? 0)) / Math.max(0.01, (beat?.end ?? duration) - (beat?.start ?? 0))),
  );

  ctx.textAlign = "center";
  ctx.fillStyle = "rgba(103,232,249,0.95)";
  ctx.font = "700 16px ui-sans-serif, system-ui";
  ctx.fillText("EXPLAINER", WIDTH / 2, 88);
  ctx.fillStyle = "#ffffff";
  ctx.font = "700 28px ui-sans-serif, system-ui";
  wrapLines(ctx, topic, WIDTH - 120, 2).forEach((line, index) => {
    ctx.fillText(line, WIDTH / 2, 126 + index * 34);
  });
  ctx.textAlign = "left";

  roundRect(ctx, x, panelTop, w, panelH, 22);
  ctx.fillStyle = "rgba(3,16,24,0.94)";
  ctx.fill();
  ctx.strokeStyle = "rgba(34,211,238,0.28)";
  ctx.lineWidth = 1.5;
  ctx.stroke();

  let chipX = x + 16;
  const chipY = panelTop + 14;
  steps.forEach((s, index) => {
    const label = `${index + 1}. ${s.title.slice(0, 16)}`;
    ctx.font = "700 10px ui-sans-serif, system-ui";
    const tw = ctx.measureText(label).width + 16;
    roundRect(ctx, chipX, chipY, tw, 20, 10);
    if (index === ai) {
      ctx.fillStyle = "rgba(251,191,36,0.35)";
      ctx.strokeStyle = "rgba(251,191,36,0.7)";
    } else if (index < ai) {
      ctx.fillStyle = "rgba(34,211,238,0.22)";
      ctx.strokeStyle = "rgba(34,211,238,0.4)";
    } else {
      ctx.fillStyle = "rgba(255,255,255,0.06)";
      ctx.strokeStyle = "rgba(255,255,255,0.12)";
    }
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = index === ai ? "#fef3c7" : index < ai ? "#cffafe" : "#71717a";
    ctx.fillText(label, chipX + 8, chipY + 14);
    chipX += tw + 6;
  });

  const cardY = chipY + 32;
  roundRect(ctx, x + 14, cardY, w - 28, 78, 14);
  ctx.fillStyle = "rgba(8,51,68,0.85)";
  ctx.fill();
  ctx.strokeStyle = "rgba(103,232,249,0.45)";
  ctx.stroke();
  ctx.fillStyle = "#fbbf24";
  ctx.font = "800 11px ui-sans-serif, system-ui";
  ctx.fillText(`PHASE · ${phase.toUpperCase()}`, x + 28, cardY + 22);
  ctx.fillStyle = "#fff";
  ctx.font = "800 18px ui-sans-serif, system-ui";
  ctx.fillText((step.title || topic).slice(0, 42), x + 28, cardY + 46);
  if (step.example || step.detail) {
    ctx.fillStyle = "rgba(165,243,252,0.9)";
    ctx.font = "500 13px ui-sans-serif, system-ui";
    ctx.fillText(String(step.example || step.detail).slice(0, 56), x + 28, cardY + 66);
  }

  const objs = [
    { id: "A", live: true, color: "#f97316" },
    { id: "B", live: true, color: "#22d3ee" },
    { id: "C", live: true, color: "#a78bfa" },
    { id: "D", live: false, color: "#34d399" },
    { id: "E", live: false, color: "#fbbf24" },
  ];
  const heapY = cardY + 98;
  roundRect(ctx, x + 14, heapY, w - 28, panelTop + panelH - heapY - 16, 14);
  ctx.fillStyle = "rgba(0,0,0,0.35)";
  ctx.fill();
  ctx.fillStyle = "rgba(253,230,138,0.85)";
  ctx.font = "800 11px ui-sans-serif, system-ui";
  ctx.fillText("HEAP", x + 28, heapY + 22);

  const countReveal = phase === "allocate" ? 2 + Math.floor(local * 3.2) : 5;
  objs.forEach((obj, index) => {
    if (index >= countReveal) return;
    let present = true;
    let dim = false;
    let marked = false;
    if (phase === "unref") {
      dim = !obj.live && local > (obj.id === "D" ? 0.25 : 0.55);
    } else if (phase === "mark") {
      dim = !obj.live;
      marked = obj.live && local > (obj.id === "A" ? 0.15 : obj.id === "B" ? 0.35 : 0.55);
    } else if (phase === "sweep") {
      if (!obj.live && local > 0.35) present = false;
      marked = obj.live;
    } else if (phase === "compact") {
      if (!obj.live) present = false;
      marked = obj.live;
    } else if (phase === "other") {
      marked = obj.live;
      dim = !obj.live;
    }
    if (!present) return;
    const ox = x + 28 + (index % 5) * 78 + (phase === "compact" && obj.live ? -index * 6 : 0);
    const oy = heapY + 40;
    roundRect(ctx, ox, oy, 64, 64, 12);
    ctx.globalAlpha = dim ? 0.4 : 1;
    ctx.fillStyle = marked ? "rgba(163,230,53,0.28)" : "rgba(255,255,255,0.06)";
    ctx.fill();
    ctx.strokeStyle = marked ? "#a3e635" : obj.color;
    ctx.lineWidth = marked ? 2.5 : 1.5;
    ctx.stroke();
    ctx.fillStyle = "#fff";
    ctx.font = "800 18px ui-monospace, monospace";
    ctx.textAlign = "center";
    ctx.fillText(obj.id, ox + 32, oy + 30);
    ctx.font = "700 10px ui-sans-serif, system-ui";
    ctx.fillStyle = marked ? "#bef264" : dim ? "#a1a1aa" : "#e4e4e7";
    ctx.fillText(marked ? "MARKED" : obj.live ? "live" : "dead", ox + 32, oy + 48);
    ctx.textAlign = "left";
    ctx.globalAlpha = 1;
  });

  const captions: Record<string, string> = {
    allocate: "new → objects land in heap",
    unref: "refs cleared → unreachable",
    mark: "GC marks reachable graph",
    sweep: "sweep frees unmarked",
    compact: "compact reduces free space",
    other: "mechanism in motion",
  };
  ctx.fillStyle = "#a1a1aa";
  ctx.font = "600 12px ui-sans-serif, system-ui";
  ctx.fillText(captions[phase] || captions.other, x + 28, panelTop + panelH - 22);
}

'''
    marker = "function drawConceptPanel("
    if marker not in text:
        raise SystemExit("drawConceptPanel not found")
    text = text.replace(marker, helper + marker, 1)

    old = """  if (wantsHashMap) {
    drawHashMapBoard(ctx, scene, elapsed, duration, topic, lesson);
    return;
  }"""
    new = """  if (wantsHashMap) {
    drawHashMapBoard(ctx, scene, elapsed, duration, topic, lesson);
    return;
  }
  const topicBlob = `${lesson?.topic || ""} ${topic || ""}`;
  if (
    (lesson?.reel_mode === "explainer" || Boolean(scene.diagram_steps?.length)) &&
    isGcTopicExport(topicBlob)
  ) {
    drawGcHeapBoard(ctx, scene, elapsed, duration, topic);
    return;
  }"""
    if old not in text:
        raise SystemExit("wantsHashMap branch not found")
    text = text.replace(old, new, 1)
    export.write_text(text)
    print("added drawGcHeapBoard + route")

print("ok")
