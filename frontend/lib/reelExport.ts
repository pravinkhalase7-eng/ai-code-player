import type { HighlightRange, Lesson, LessonScene } from "@/types/lesson";
import { audioSrc } from "@/lib/utils";
import { visemeAt, VISEME_MOUTH } from "@/lib/viseme";
import { buildCues, cueAt } from "@/lib/narrationSync";
import { beatHighlight, reelBeatAt, reelBeats } from "@/lib/reelDebugSync";

const WIDTH = 720;
const HEIGHT = 1280;

function pickRecorderMime(): string {
  const types = [
    "video/webm;codecs=vp9,opus",
    "video/webm;codecs=vp8,opus",
    "video/webm",
    "video/mp4",
  ];
  return types.find((type) => typeof MediaRecorder !== "undefined" && MediaRecorder.isTypeSupported(type)) || "";
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

function drawFrame(
  ctx: CanvasRenderingContext2D,
  lesson: Lesson,
  scene: LessonScene,
  elapsed: number,
  duration: number,
  code: string,
) {
  drawStudioBackground(ctx);
  const debugging = scene.type === "execution" || scene.type === "terminal";
  const beats = debugging ? reelBeats(scene, code, duration) : [];
  const beat = debugging ? reelBeatAt(beats, elapsed) : null;
  const cue = cueAt(buildCues(scene, duration), elapsed);
  const highlight = debugging
    ? beatHighlight(beat)
    : (cue?.highlight ?? scene.highlight_ranges?.[0] ?? null);
  const caption =
    debugging && beat?.description ? beat.description : cue?.text || scene.narration || "";
  const outputLines = beat?.output ?? [];
  const vars = (beat?.variables || []).slice(0, 3).map((item) => `${item.name}=${item.value}`).join("  ");

  ctx.textAlign = "center";
  ctx.fillStyle = "rgba(165,243,252,0.82)";
  ctx.font = "700 13px ui-sans-serif, system-ui";
  ctx.fillText(lesson.language.toUpperCase(), WIDTH / 2, 36);
  ctx.fillStyle = "#ffffff";
  ctx.font = "700 20px ui-sans-serif, system-ui";
  wrapLines(ctx, lesson.topic, WIDTH - 80, 2).forEach((line, index) => {
    ctx.fillText(line, WIDTH / 2, 62 + index * 24);
  });
  ctx.textAlign = "left";

  const footer = 220;
  const headerBottom = 88;
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
    WIDTH - 56,
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

  const viseme = visemeAt(scene.narration || "", elapsed, true, duration);
  drawByte(ctx, 16, HEIGHT - 236, 0.82, viseme);
  ctx.fillStyle = "rgba(165,243,252,0.9)";
  ctx.font = "700 11px ui-sans-serif, system-ui";
  ctx.fillText("BYTE", 58, HEIGHT - 72);

  ctx.fillStyle = "rgba(0,0,0,0.62)";
  roundRect(ctx, 148, HEIGHT - 148, WIDTH - 176, 92, 18);
  ctx.fill();
  ctx.strokeStyle = "rgba(255,255,255,0.1)";
  ctx.lineWidth = 1;
  ctx.stroke();
  ctx.fillStyle = "#fff";
  ctx.font = "600 18px ui-sans-serif, system-ui";
  wrapLines(ctx, caption, WIDTH - 214, 3).forEach((line, index) => {
    ctx.fillText(line, 164, HEIGHT - 116 + index * 22);
  });
  if (highlight?.label) {
    ctx.fillStyle = "#fcd34d";
    ctx.font = "700 11px ui-sans-serif, system-ui";
    ctx.fillText(highlight.label.toUpperCase(), 164, HEIGHT - 68);
  }
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

export type ReelExportProgress = { scene: number; total: number; label: string };

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
      const started = performance.now();
      await new Promise<void>((resolve) => {
        const tick = () => {
          const elapsed = (performance.now() - started) / 1000;
          drawFrame(ctx, lesson, scene, elapsed, duration, lastCode);
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

  return stopped;
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
  if (blob.type.includes("mp4")) return "mp4";
  return "webm";
}
