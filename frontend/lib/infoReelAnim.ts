/** Timing helpers for explain/info reel concept animations. */

export type AnimBeat = {
  text: string;
  index: number;
  start: number;
  end: number;
};

export function infoBulletBeats(bullets: string[], duration: number): AnimBeat[] {
  const items = (bullets || []).map((text) => String(text || "").trim()).filter(Boolean);
  const count = Math.max(1, items.length || 1);
  const span = Math.max(duration || 1, 0.5);
  const slice = span / count;
  return items.map((text, index) => ({
    text,
    index,
    start: index * slice,
    end: index === count - 1 ? span + 0.05 : (index + 1) * slice,
  }));
}

/** Prefer real narration segment times; squeeze/stretch to match actual clip duration. */
export function beatsFromSegments(
  segments: { start: number; end: number; text?: string }[],
  duration?: number,
): AnimBeat[] {
  const segs = (segments || [])
    .map((s, index) => ({
      text: String(s.text || "").trim(),
      index,
      start: Math.max(0, Number(s.start) || 0),
      end: Math.max(Number(s.start) || 0, Number(s.end) || 0),
    }))
    .filter((s) => s.end > s.start + 0.05);
  if (!segs.length) return [];
  const last = segs[segs.length - 1];
  const dur = Number(duration) || 0;
  // Planned cue clocks often overshoot short TTS (or undershoot padded files).
  if (dur > 0.4 && last.end > 0.05 && Math.abs(dur - last.end) > 0.45) {
    const scale = dur / last.end;
    return segs.map((s, index) => ({
      ...s,
      index,
      start: Math.max(0, Number((s.start * scale).toFixed(3))),
      end:
        index === segs.length - 1
          ? Number(dur.toFixed(3))
          : Math.max(0.05, Number((s.end * scale).toFixed(3))),
    }));
  }
  // Only extend last beat if duration is near the cue end (not minutes of silence).
  if (dur > last.end + 0.2 && dur <= last.end + 2.5) {
    last.end = dur;
  }
  return segs;
}

export function infoBulletAtBeats(
  beats: AnimBeat[],
  currentTime: number,
): { active: number; visibleCount: number; beats: AnimBeat[] } {
  if (!beats.length) return { active: 0, visibleCount: 0, beats };
  const t = Math.max(0, currentTime);
  let active = beats.findIndex((beat) => t >= beat.start && t < beat.end);
  if (active < 0) active = t >= beats[beats.length - 1].end ? beats.length - 1 : 0;
  return { active, visibleCount: active + 1, beats };
}

export function infoBulletAt(
  bullets: string[],
  currentTime: number,
  duration: number,
): { active: number; visibleCount: number; beats: AnimBeat[] } {
  return infoBulletAtBeats(infoBulletBeats(bullets, duration), currentTime);
}

/** Soft UI blip when a bullet becomes active (browser only). */
export function playInfoBulletBlip() {
  if (typeof window === "undefined") return;
  try {
    const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (!AudioCtx) return;
    const ctx = new AudioCtx();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = "sine";
    osc.frequency.setValueAtTime(660, ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.08);
    gain.gain.setValueAtTime(0.0001, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.045, ctx.currentTime + 0.02);
    gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.16);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.18);
    window.setTimeout(() => void ctx.close(), 300);
  } catch {
    /* ignore autoplay / unsupported */
  }
}
