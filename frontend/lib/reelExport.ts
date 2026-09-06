import type { HighlightRange, Lesson, LessonScene } from "@/types/lesson";
import { audioSrc } from "@/lib/utils";
import { visemeAt, VISEME_MOUTH } from "@/lib/viseme";
import { buildCues, cueAt } from "@/lib/narrationSync";
import { beatHighlight, reelBeatAt, reelBeats } from "@/lib/reelDebugSync";
import { displayTopic, stripDurationNoise } from "@/lib/reelHeadlines";
import { isPosterScene, reelCta } from "@/lib/reelCta";
import { infoBulletAt } from "@/lib/infoReelAnim";

const WIDTH = 720;
const HEIGHT = 1280;

export type ReelExportProgress = { scene: number; total: number; label: string };

function pickRecorderMime(): string {
  const types = [
    "video/mp4",
    "video/mp4;codecs=avc1,mp4a.40.2",
    "video/webm;codecs=vp9,opus",
    "video/webm;codecs=vp8,opus",
    "video/webm",
  ];
  return types.find((type) => typeof MediaRecorder !== "undefined" && MediaRecorder.isTypeSupported(type)) || "";
}

let ffmpegInstance: import("@ffmpeg/ffmpeg").FFmpeg | null = null;
let ffmpegLoading: Promise<import("@ffmpeg/ffmpeg").FFmpeg> | null = null;

async function getFFmpeg(onLog?: (message: string) => void) {
  if (ffmpegInstance) return ffmpegInstance;
  if (ffmpegLoading) return ffmpegLoading;
  ffmpegLoading = (async () => {
    const { FFmpeg } = await import("@ffmpeg/ffmpeg");
    const { toBlobURL } = await import("@ffmpeg/util");
    const ffmpeg = new FFmpeg();
    ffmpeg.on("log", ({ message }) => onLog?.(message));
    const baseURL = "https://unpkg.com/@ffmpeg/core@0.12.10/dist/esm";
    await ffmpeg.load({
      coreURL: await toBlobURL(`${baseURL}/ffmpeg-core.js`, "text/javascript"),
      wasmURL: await toBlobURL(`${baseURL}/ffmpeg-core.wasm`, "application/wasm"),
    });
    ffmpegInstance = ffmpeg;
    return ffmpeg;
  })();
  try {
    return await ffmpegLoading;
  } finally {
    ffmpegLoading = null;
  }
}

function isMp4Blob(blob: Blob): boolean {
  return /mp4|m4v|quicktime/i.test(blob.type || "");
}

async function convertBlobToMp4(
  blob: Blob,
  onProgress?: (progress: ReelExportProgress) => void,
): Promise<Blob> {
  if (isMp4Blob(blob)) return blob;
  onProgress?.({ scene: 0, total: 0, label: "Converting to MP4…" });
  const { fetchFile } = await import("@ffmpeg/util");
  const ffmpeg = await getFFmpeg();
  const inputName = blob.type.includes("webm") ? "input.webm" : "input.bin";
  await ffmpeg.writeFile(inputName, await fetchFile(blob));
  await ffmpeg.exec([
    "-i",
    inputName,
    "-c:v",
    "libx264",
    "-preset",
    "ultrafast",
    "-pix_fmt",
    "yuv420p",
    "-c:a",
    "aac",
    "-movflags",
    "+faststart",
    "output.mp4",
  ]);
  const data = await ffmpeg.readFile("output.mp4");
  try {
    await ffmpeg.deleteFile(inputName);
  } catch {
    /* ignore cleanup errors */
  }
  try {
    await ffmpeg.deleteFile("output.mp4");
  } catch {
    /* ignore cleanup errors */
  }
  const raw = data instanceof Uint8Array ? data : new TextEncoder().encode(String(data));
  const bytes = new Uint8Array(raw.byteLength);
  bytes.set(raw);
  return new Blob([bytes], { type: "video/mp4" });
}

async function decodeAudio(ctx: AudioContext, url: string | undefined): Promise<AudioBuffer | null> {
  if (!url) return null;
  try {
    const response = await fetch(url);
    const bytes = await response.arrayBuffer();
    return await ctx.decodeAudioData(bytes.slice(0));
  } catch {
    return null;
  }
}

function wrapLines(ctx: CanvasRenderingContext2D, text: string, maxWidth: number, maxLines = 4): string[] {
  const words = text.split(/\s+/).filter(Boolean);
  const lines: string[] = [];
  let current = "";
  for (const word of words) {
    const next = current ? `${current} ${word}` : word;
    if (ctx.measureText(next).width > maxWidth && current) {
      lines.push(current);
      current = word;
      if (lines.length >= maxLines) break;
    } else {
      current = next;
    }
  }
  if (current && lines.length < maxLines) lines.push(current);
  return lines;
}

const WATERMARK_SRC = "/techshala-logo.png";

function loadImage(url: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error("image"));
    image.src = url;
  });
}

async function fetchImage(url: string): Promise<HTMLImageElement | null> {
  try {
    const response = await fetch(url);
    if (!response.ok) return null;
    const blob = await response.blob();
    return await loadImage(URL.createObjectURL(blob));
  } catch {
    return null;
  }
}

async function loadWatermark(): Promise<HTMLCanvasElement | null> {
  const image = await fetchImage(WATERMARK_SRC);
  if (!image) return null;
  const canvas = document.createElement("canvas");
  canvas.width = image.width;
  canvas.height = image.height;
  const ink = canvas.getContext("2d");
  if (!ink) return null;
  // Logo is already a transparent PNG — keep white wordmark pixels intact.
  ink.drawImage(image, 0, 0);
  return canvas;
}

function drawWatermark(ctx: CanvasRenderingContext2D, mark: HTMLCanvasElement | null) {
  if (!mark) return;
  const width = 112;
  const height = width * (mark.height / Math.max(1, mark.width));
  const x = WIDTH - width - 20;
  const y = 48;
  ctx.save();
  ctx.shadowColor = "rgba(0,0,0,0.55)";
  ctx.shadowBlur = 18;
  ctx.globalAlpha = 0.96;
  ctx.drawImage(mark, x, y, width, height);
  ctx.restore();
}

async function loadThumb(url?: string | null): Promise<HTMLImageElement | null> {
  if (!url) return null;
  return fetchImage(url);
}

function drawCoverImage(ctx: CanvasRenderingContext2D, image: HTMLImageElement | null) {
  if (!image) return false;
  const scale = Math.max(WIDTH / image.width, HEIGHT / image.height);
  const width = image.width * scale;
  const height = image.height * scale;
  ctx.drawImage(image, (WIDTH - width) / 2, (HEIGHT - height) / 2, width, height);
  const top = ctx.createLinearGradient(0, 0, 0, 180);
  top.addColorStop(0, "rgba(0,0,0,0.72)");
  top.addColorStop(1, "transparent");
  ctx.fillStyle = top;
  ctx.fillRect(0, 0, WIDTH, 180);
  const bottom = ctx.createLinearGradient(0, HEIGHT - 320, 0, HEIGHT);
  bottom.addColorStop(0, "transparent");
  bottom.addColorStop(1, "rgba(0,0,0,0.78)");
  ctx.fillStyle = bottom;
  ctx.fillRect(0, HEIGHT - 320, WIDTH, 320);
  return true;
}

function drawProgress(
  ctx: CanvasRenderingContext2D,
  sceneIndex: number,
  sceneCount: number,
  progress: number,
) {
  const count = Math.max(1, sceneCount);
  const gap = 6;
  const left = 24;
  const width = WIDTH - 48;
  const unit = (width - gap * (count - 1)) / count;
  for (let index = 0; index < count; index += 1) {
    const x = left + index * (unit + gap);
    ctx.fillStyle = "rgba(255,255,255,0.25)";
    roundRect(ctx, x, 18, unit, 4, 2);
    ctx.fill();
    const fill =
      index < sceneIndex ? 1 : index === sceneIndex ? Math.min(1, Math.max(0, progress)) : 0;
    if (fill > 0) {
      ctx.fillStyle = "#ffffff";
      roundRect(ctx, x, 18, unit * fill, 4, 2);
      ctx.fill();
    }
  }
}

function drawFollowChip(ctx: CanvasRenderingContext2D, handle: string) {
  ctx.textAlign = "left";
  ctx.fillStyle = "#ffffff";
  ctx.font = "700 18px ui-sans-serif, system-ui";
  const handleW = ctx.measureText(handle).width;
  ctx.fillText(handle, 28, 52);
  const label = "FOLLOW";
  ctx.font = "800 12px ui-sans-serif, system-ui";
  const w = ctx.measureText(label).width + 22;
  ctx.fillStyle = "#fbbf24";
  roundRect(ctx, 28 + handleW + 14, 36, w, 22, 11);
  ctx.fill();
  ctx.fillStyle = "#18181b";
  ctx.fillText(label, 28 + handleW + 25, 52);
}

function drawStudioBackground(ctx: CanvasRenderingContext2D) {
  ctx.fillStyle = "#05070d";
  ctx.fillRect(0, 0, WIDTH, HEIGHT);
  const amber = ctx.createRadialGradient(WIDTH * 0.5, -40, 20, WIDTH * 0.5, -40, HEIGHT * 0.5);
  amber.addColorStop(0, "rgba(251,191,36,0.34)");
  amber.addColorStop(1, "transparent");
  ctx.fillStyle = amber;
  ctx.fillRect(0, 0, WIDTH, HEIGHT);
  const cyan = ctx.createRadialGradient(WIDTH * 0.5, HEIGHT + 40, 20, WIDTH * 0.5, HEIGHT + 40, HEIGHT * 0.48);
  cyan.addColorStop(0, "rgba(8,145,178,0.26)");
  cyan.addColorStop(1, "transparent");
  ctx.fillStyle = cyan;
  ctx.fillRect(0, 0, WIDTH, HEIGHT);
  const center = ctx.createRadialGradient(WIDTH * 0.5, HEIGHT * 0.36, 10, WIDTH * 0.5, HEIGHT * 0.36, HEIGHT * 0.42);
  center.addColorStop(0, "rgba(255,255,255,0.05)");
  center.addColorStop(1, "transparent");
  ctx.fillStyle = center;
  ctx.fillRect(0, 0, WIDTH, HEIGHT);
}

function drawIdeWindow(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  filename: string,
  code: string,
  highlight: HighlightRange | null,
  output?: { label: string; condition?: string; stopped?: boolean; variables: string; lines: string[]; latest?: string },
) {
  const titleH = 38;
  const consoleH = output ? Math.min(158, 52 + Math.max(1, output.lines.length) * 20) : 0;
  const codeH = Math.max(80, h - titleH - consoleH);

  roundRect(ctx, x, y, w, h, 22);
  ctx.fillStyle = "rgba(7,17,31,0.94)";
  ctx.fill();
  ctx.strokeStyle = "rgba(165,243,252,0.22)";
  ctx.lineWidth = 1.5;
  ctx.stroke();
  ctx.save();
  roundRect(ctx, x, y, w, h, 22);
  ctx.clip();

  ctx.fillStyle = "rgba(255,255,255,0.06)";
  roundRect(ctx, x, y, w, titleH, 22);
  ctx.fill();
  ctx.fillRect(x, y + 16, w, titleH - 16);

  const dots = ["#f87171", "#fcd34d", "#34d399"];
  dots.forEach((color, index) => {
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(x + 22 + index * 14, y + titleH / 2, 5, 0, Math.PI * 2);
    ctx.fill();
  });
  ctx.fillStyle = "#d4d4d8";
  ctx.font = "600 13px ui-sans-serif, system-ui";
  ctx.fillText(filename, x + 72, y + 24);

  ctx.strokeStyle = "rgba(255,255,255,0.08)";
  ctx.beginPath();
  ctx.moveTo(x, y + titleH);
  ctx.lineTo(x + w, y + titleH);
  ctx.stroke();

  const lines = code.replace(/\n$/, "").split("\n");
  const innerW = w - 28;
  const innerH = codeH - 16;
  let fontSize = 15;
  while (fontSize > 9) {
    ctx.font = `${fontSize}px ui-monospace, SFMono-Regular, Menlo, monospace`;
    const maxW = Math.max(0, ...lines.map((line) => ctx.measureText((line || " ").slice(0, 140)).width));
    const totalH = lines.length * (fontSize + 6);
    if (maxW + 36 <= innerW && totalH <= innerH) break;
    fontSize -= 0.5;
  }
  const lineH = fontSize + 6;
  ctx.save();
  ctx.beginPath();
  ctx.rect(x + 6, y + titleH + 4, w - 12, codeH - 8);
  ctx.clip();
  ctx.font = `${fontSize}px ui-monospace, SFMono-Regular, Menlo, monospace`;
  lines.forEach((line, index) => {
    const lineNo = index + 1;
    const top = y + titleH + 22 + index * lineH;
    const active = Boolean(highlight && lineNo >= highlight.start_line && lineNo <= highlight.end_line);
    if (active) {
      ctx.fillStyle = "rgba(251,191,36,0.28)";
      roundRect(ctx, x + 10, top - fontSize + 2, w - 20, lineH, 5);
      ctx.fill();
      ctx.strokeStyle = "rgba(252,211,77,0.5)";
      ctx.lineWidth = 1;
      ctx.stroke();
    }
    ctx.fillStyle = active ? "#fbbf24" : "#52525b";
    ctx.fillText(String(lineNo), x + 18, top);
    ctx.fillStyle = active ? "#fff7ed" : "#e4e4e7";
    ctx.fillText(line || " ", x + 48, top);
  });
  ctx.restore();

  if (output) {
    const cy = y + titleH + codeH;
    ctx.strokeStyle = "rgba(251,191,36,0.28)";
    ctx.beginPath();
    ctx.moveTo(x, cy);
    ctx.lineTo(x + w, cy);
    ctx.stroke();
    ctx.fillStyle = "rgba(0,0,0,0.45)";
    ctx.fillRect(x + 1, cy, w - 2, h - titleH - codeH - 1);

    ctx.fillStyle = "#fcd34d";
    ctx.font = "700 11px ui-sans-serif, system-ui";
    ctx.fillText(output.label, x + 18, cy + 20);
    if (output.variables) {
      ctx.fillStyle = "#fde68a";
      ctx.font = "500 11px ui-monospace, monospace";
      ctx.fillText(output.variables, x + 18 + ctx.measureText(output.label).width + 12, cy + 20);
    }
    let cursor = cy + 40;
    if (output.condition) {
      ctx.fillStyle = "#a1a1aa";
      ctx.font = "500 12px ui-monospace, monospace";
      ctx.fillText(`${output.condition}${output.stopped ? " · stop" : ""}`, x + 18, cursor);
      cursor += 18;
    }
    const shown = output.lines.slice(-5);
    if (!shown.length) {
      ctx.fillStyle = "#71717a";
      ctx.font = "500 13px ui-monospace, monospace";
      ctx.fillText("waiting for print…", x + 18, cursor);
    } else {
      shown.forEach((line) => {
        const last = line === output.latest;
        ctx.fillStyle = last ? "#fde68a" : "#d4d4d8";
        ctx.font = `${last ? "600" : "500"} 14px ui-monospace, monospace`;
        ctx.fillText(`> ${line}`, x + 18, cursor);
        cursor += 18;
      });
    }
  }

  ctx.restore();
}

function drawByte(ctx: CanvasRenderingContext2D, x: number, y: number, scale: number, viseme: ReturnType<typeof visemeAt>) {
  const mouth = VISEME_MOUTH[viseme];
  ctx.save();
  ctx.translate(x, y);
  ctx.scale(scale, scale);
  ctx.fillStyle = "rgba(34,211,238,0.18)";
  ctx.beginPath();
  ctx.ellipse(64, 160, 28, 6, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = "#67e8f9";
  ctx.beginPath();
  ctx.arc(64, 12, 6, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = "#a1a1aa";
  roundRect(ctx, 62, 16, 4, 14, 2);
  ctx.fill();
  ctx.fillStyle = "#f59e0b";
  roundRect(ctx, 22, 48, 12, 22, 6);
  ctx.fill();
  roundRect(ctx, 94, 48, 12, 22, 6);
  ctx.fill();
  ctx.fillStyle = "#fbbf24";
  roundRect(ctx, 28, 28, 72, 68, 24);
  ctx.fill();
  ctx.fillStyle = "#0b1220";
  roundRect(ctx, 36, 44, 56, 42, 14);
  ctx.fill();
  ctx.fillStyle = "#67e8f9";
  roundRect(ctx, 44, 52, 16, 9, 3);
  ctx.fill();
  roundRect(ctx, 68, 52, 16, 9, 3);
  ctx.fill();
  ctx.fillStyle = "#7c2d12";
  ctx.beginPath();
  ctx.ellipse(64, mouth.cy, mouth.rx, mouth.ry, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = "#27272a";
  ctx.beginPath();
  ctx.moveTo(38, 94);
  ctx.bezierCurveTo(46, 102, 56, 106, 64, 106);
  ctx.bezierCurveTo(72, 106, 82, 102, 90, 94);
  ctx.lineTo(104, 148);
  ctx.lineTo(24, 148);
  ctx.closePath();
  ctx.fill();
  ctx.fillStyle = "#3f3f46";
  roundRect(ctx, 50, 108, 28, 44, 8);
  ctx.fill();
  ctx.fillStyle = "#fbbf24";
  ctx.beginPath();
  ctx.arc(64, 132, 11, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
}



function scheduleConceptBlips(audioCtx: AudioContext, dest: MediaStreamAudioDestinationNode, scene: LessonScene, duration: number) {
  if (scene.type !== "concept") return;
  const beats = infoBulletAt(scene.bullets || [], 0, duration).beats;
  for (const beat of beats) {
    const when = audioCtx.currentTime + Math.max(0.02, beat.start);
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = "sine";
    osc.frequency.setValueAtTime(660, when);
    osc.frequency.exponentialRampToValueAtTime(880, when + 0.08);
    gain.gain.setValueAtTime(0.0001, when);
    gain.gain.exponentialRampToValueAtTime(0.04, when + 0.02);
    gain.gain.exponentialRampToValueAtTime(0.0001, when + 0.16);
    osc.connect(gain);
    gain.connect(dest);
    osc.start(when);
    osc.stop(when + 0.18);
  }
}

function drawConceptPanel(
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
}

function drawFrame(
  ctx: CanvasRenderingContext2D,
  lesson: Lesson,
  scene: LessonScene,
  elapsed: number,
  duration: number,
  code: string,
  thumb: HTMLImageElement | null,
  sceneIndex: number,
  sceneCount: number,
  watermark: HTMLCanvasElement | null,
) {
  const poster = isPosterScene(scene.type);
  if (poster) {
    if (!drawCoverImage(ctx, thumb)) drawStudioBackground(ctx);
  } else {
    drawStudioBackground(ctx);
  }
  const debugging = scene.type === "execution" || scene.type === "terminal";
  const beats = debugging ? reelBeats(scene, code, duration) : [];
  const beat = debugging ? reelBeatAt(beats, elapsed) : null;
  const cue = cueAt(buildCues(scene, duration), elapsed);
  const highlight = debugging ? beatHighlight(beat) : (cue?.highlight ?? null);
  const caption = stripDurationNoise(cue?.text || scene.narration || "");
  const outputLines = beat?.output ?? [];
  const vars = (beat?.variables || []).slice(0, 3).map((item) => `${item.name}=${item.value}`).join("  ");
  const topic = displayTopic(lesson.topic);
  const cta = reelCta(lesson, scene);

  drawProgress(ctx, sceneIndex, sceneCount, duration > 0 ? elapsed / duration : 0);
  drawFollowChip(ctx, cta.handle);

  if (poster) {
    ctx.textAlign = "center";
    if (scene.type === "summary") {
      ctx.fillStyle = "rgba(0,0,0,0.72)";
      roundRect(ctx, 40, HEIGHT - 430, WIDTH - 160, 210, 24);
      ctx.fill();
      ctx.fillStyle = "#fcd34d";
      ctx.font = "700 14px ui-sans-serif, system-ui";
      ctx.fillText("SAVE THIS", WIDTH / 2 - 40, HEIGHT - 388);
      ctx.fillStyle = "#ffffff";
      ctx.font = "800 28px ui-sans-serif, system-ui";
      wrapLines(ctx, cta.endLine, WIDTH - 220, 2).forEach((line, index) => {
        ctx.fillText(line, WIDTH / 2 - 40, HEIGHT - 348 + index * 34);
      });
      const pulse = 1 + 0.04 * Math.sin(elapsed * 6);
      ctx.save();
      ctx.translate(WIDTH / 2 - 40, HEIGHT - 268);
      ctx.scale(pulse, pulse);
      ctx.fillStyle = "#fbbf24";
      roundRect(ctx, -150, -22, 300, 44, 22);
      ctx.fill();
      ctx.fillStyle = "#18181b";
      ctx.font = "800 16px ui-sans-serif, system-ui";
      ctx.fillText(cta.endAction, 0, 6);
      ctx.restore();
      ctx.fillStyle = "#e4e4e7";
      ctx.font = "600 16px ui-sans-serif, system-ui";
      wrapLines(ctx, cta.comment, WIDTH - 220, 2).forEach((line, index) => {
        ctx.fillText(line, WIDTH / 2 - 40, HEIGHT - 228 + index * 22);
      });
    } else if (!thumb) {
      ctx.fillStyle = "rgba(165,243,252,0.95)";
      ctx.font = "700 16px ui-sans-serif, system-ui";
      ctx.fillText(lesson.language.toUpperCase(), WIDTH / 2, 240);
      ctx.fillStyle = "#ffffff";
      ctx.font = "800 44px ui-sans-serif, system-ui";
      wrapLines(ctx, topic, WIDTH - 100, 3).forEach((line, index) => {
        ctx.fillText(line, WIDTH / 2, 310 + index * 52);
      });
    }
    ctx.textAlign = "left";
  } else if (scene.type === "concept" || lesson.requires_code === false) {
    drawConceptPanel(ctx, scene, elapsed, duration, topic);
  } else {
    ctx.textAlign = "center";
    ctx.fillStyle = "rgba(165,243,252,0.9)";
    ctx.font = "700 16px ui-sans-serif, system-ui";
    ctx.fillText(lesson.language.toUpperCase(), WIDTH / 2, 88);
    ctx.fillStyle = "#ffffff";
    ctx.font = "700 28px ui-sans-serif, system-ui";
    wrapLines(ctx, topic, WIDTH - 120, 2).forEach((line, index) => {
      ctx.fillText(line, WIDTH / 2, 126 + index * 34);
    });
    ctx.textAlign = "left";

    const footer = 220;
    const headerBottom = 188;
    const available = HEIGHT - footer - headerBottom;
    const lineCount = Math.max(1, (code || " ").replace(/\n$/, "").split("\n").length);
    const consoleH = debugging ? Math.min(158, 52 + Math.max(1, outputLines.length) * 20) : 0;
    const ideH = Math.min(available, Math.max(220, 38 + lineCount * 22 + 24 + consoleH));
    const ideTop = headerBottom + Math.max(0, (available - ideH) / 2);
    const filename = scene.filename || "Main.java";
    drawIdeWindow(
      ctx,
      28,
      ideTop,
      WIDTH - 108,
      ideH,
      filename,
      code,
      highlight,
      debugging
        ? {
            label: beat ? `OUTPUT  ·  ${beat.label}` : "OUTPUT",
            condition: beat?.condition
              ? `${beat.condition} → ${beat.condition_result ? "true" : "false"}`
              : undefined,
            stopped: beat?.stopped,
            variables: vars,
            lines: outputLines,
            latest: beat?.latest,
          }
        : undefined,
    );
  }

  const viseme = visemeAt(scene.narration || "", elapsed, true, duration);
  drawByte(ctx, 16, HEIGHT - 236, 0.82, viseme);
  ctx.fillStyle = "rgba(165,243,252,0.9)";
  ctx.font = "700 11px ui-sans-serif, system-ui";
  ctx.fillText("BYTE", 58, HEIGHT - 72);

  ctx.fillStyle = "rgba(0,0,0,0.62)";
  roundRect(ctx, 148, HEIGHT - 148, WIDTH - 230, 92, 18);
  ctx.fill();
  ctx.strokeStyle = "rgba(255,255,255,0.1)";
  ctx.lineWidth = 1;
  ctx.stroke();
  ctx.fillStyle = "#fff";
  ctx.font = "600 18px ui-sans-serif, system-ui";
  wrapLines(ctx, caption, WIDTH - 268, 3).forEach((line, index) => {
    ctx.fillText(line, 164, HEIGHT - 116 + index * 22);
  });
  drawWatermark(ctx, watermark);
}

function roundRect(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  r: number,
) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}


export async function exportReelVideo(
  lesson: Lesson,
  onProgress?: (progress: ReelExportProgress) => void,
): Promise<Blob> {
  const canvas = document.createElement("canvas");
  canvas.width = WIDTH;
  canvas.height = HEIGHT;
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("Could not create a video canvas.");

  const mime = pickRecorderMime();
  if (!mime || typeof MediaRecorder === "undefined") {
    throw new Error("This browser cannot record a reel video. Try Chrome or Edge.");
  }

  const audioCtx = new AudioContext();
  await audioCtx.resume();
  const dest = audioCtx.createMediaStreamDestination();
  const canvasStream = canvas.captureStream(30);
  const mixed = new MediaStream([
    ...canvasStream.getVideoTracks(),
    ...dest.stream.getAudioTracks(),
  ]);
  const recorder = new MediaRecorder(mixed, { mimeType: mime, videoBitsPerSecond: 3_500_000 });
  const chunks: BlobPart[] = [];
  recorder.ondataavailable = (event) => {
    if (event.data.size) chunks.push(event.data);
  };
  const stopped = new Promise<Blob>((resolve, reject) => {
    recorder.onstop = () => resolve(new Blob(chunks, { type: mime }));
    recorder.onerror = () => reject(new Error("Reel recording failed."));
  });
  recorder.start(200);

  const scenes = lesson.scenes;
  let lastCode = scenes.find((item) => item.code?.trim())?.code || "";
  const thumb = await loadThumb(lesson.thumbnail_url);
  const watermark = await loadWatermark();

  try {
    for (let index = 0; index < scenes.length; index += 1) {
      const scene = scenes[index];
      if (scene.code?.trim()) lastCode = scene.code;
      onProgress?.({ scene: index + 1, total: scenes.length, label: scene.type });
      const buffer = await decodeAudio(audioCtx, audioSrc(scene.audio_url));
      const duration = buffer?.duration || scene.duration || 5;
      if (buffer) {
        const source = audioCtx.createBufferSource();
        source.buffer = buffer;
        source.connect(dest);
        const mute = audioCtx.createGain();
        mute.gain.value = 0;
        source.connect(mute);
        mute.connect(audioCtx.destination);
        source.start();
      }
      scheduleConceptBlips(audioCtx, dest, scene, duration);
      const started = performance.now();
      await new Promise<void>((resolve) => {
        const tick = () => {
          const elapsed = (performance.now() - started) / 1000;
          drawFrame(ctx, lesson, scene, elapsed, duration, lastCode, thumb, index, scenes.length, watermark);
          if (elapsed >= duration) {
            resolve();
            return;
          }
          requestAnimationFrame(tick);
        };
        tick();
      });
    }
  } finally {
    if (recorder.state !== "inactive") recorder.stop();
    void audioCtx.close();
  }

  const recorded = await stopped;
  if (isMp4Blob(recorded)) return recorded;
  try {
    return await convertBlobToMp4(recorded, onProgress);
  } catch (error) {
    console.warn("MP4 conversion failed; falling back to recorded blob", error);
    onProgress?.({
      scene: scenes.length,
      total: scenes.length,
      label: "Conversion failed — saving original format",
    });
    return recorded;
  }
}

export function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 4000);
}

export function fileExtension(blob: Blob): string {
  if (isMp4Blob(blob) || blob.type.includes("mp4")) return "mp4";
  return "webm";
}

/** Prefer .mp4 for reel downloads; keep webm only when conversion failed. */
export function reelDownloadName(topic: string, blob: Blob): string {
  const slug = topic.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  return `reel-${slug || "short"}.${fileExtension(blob)}`;
}
