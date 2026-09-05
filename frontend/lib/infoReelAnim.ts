/** Timing helpers for explain/info reel concept animations. */

export function infoBulletBeats(bullets: string[], duration: number) {
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

export function infoBulletAt(
  bullets: string[],
  currentTime: number,
  duration: number,
): { active: number; visibleCount: number; beats: ReturnType<typeof infoBulletBeats> } {
  const beats = infoBulletBeats(bullets, duration);
  if (!beats.length) return { active: 0, visibleCount: 0, beats };
  const t = Math.max(0, currentTime);
  let active = beats.findIndex((beat) => t >= beat.start && t < beat.end);
  if (active < 0) active = beats.length - 1;
  return { active, visibleCount: active + 1, beats };
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
