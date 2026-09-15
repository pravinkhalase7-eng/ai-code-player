/** Find where speech actually starts/ends in a decoded clip (skip TTS tail silence). */

export type SpeechBounds = {
  start: number;
  end: number;
};

const FRAME_SEC = 0.02;
const LEAD_SEC = 0.04;
const TAIL_SEC = 0.08;
const ABS_FLOOR = 0.014;
const PEAK_RATIO = 0.08;

function channelRms(channel: Float32Array, sampleRate: number): number[] {
  const frame = Math.max(1, Math.floor(sampleRate * FRAME_SEC));
  const values: number[] = [];
  for (let index = 0; index < channel.length; index += frame) {
    const end = Math.min(channel.length, index + frame);
    let sum = 0;
    for (let cursor = index; cursor < end; cursor += 1) sum += channel[cursor] * channel[cursor];
    values.push(Math.sqrt(sum / Math.max(1, end - index)));
  }
  return values;
}

export function speechBounds(channel: Float32Array, sampleRate: number): SpeechBounds {
  const duration = channel.length / Math.max(1, sampleRate);
  const rms = channelRms(channel, sampleRate);
  if (!rms.length) return { start: 0, end: duration };
  const peak = Math.max(...rms, 0);
  const floor = Math.max(ABS_FLOOR, peak * PEAK_RATIO);
  const first = rms.findIndex((value) => value >= floor);
  let last = -1;
  for (let index = rms.length - 1; index >= 0; index -= 1) {
    if (rms[index] >= floor) {
      last = index;
      break;
    }
  }
  if (first < 0 || last < 0) return { start: 0, end: duration };
  const frame = Math.max(1, Math.floor(sampleRate * FRAME_SEC));
  const start = Math.max(0, (first * frame) / sampleRate - LEAD_SEC);
  const end = Math.min(duration, ((last + 1) * frame) / sampleRate + TAIL_SEC);
  return { start, end: Math.max(start + 0.2, end) };
}

export function sliceAudioBuffer(ctx: AudioContext, buffer: AudioBuffer, bounds: SpeechBounds): AudioBuffer {
  const rate = buffer.sampleRate;
  const startSample = Math.max(0, Math.floor(bounds.start * rate));
  const endSample = Math.min(buffer.length, Math.max(startSample + 1, Math.ceil(bounds.end * rate)));
  const kept = Math.max(1, endSample - startSample);
  if (startSample <= rate * 0.02 && endSample >= buffer.length - rate * 0.02) return buffer;
  const sliced = ctx.createBuffer(buffer.numberOfChannels, kept, rate);
  for (let channelIndex = 0; channelIndex < buffer.numberOfChannels; channelIndex += 1) {
    sliced.copyToChannel(buffer.getChannelData(channelIndex).subarray(startSample, endSample), channelIndex);
  }
  return sliced;
}

const speechEndCache = new Map<string, number>();

/** Decode a clip once and return the last voiced second (for karaoke + scene clocks). */
export async function measureSpeechEnd(url: string): Promise<number | null> {
  if (!url) return null;
  const cached = speechEndCache.get(url);
  if (cached) return cached;
  try {
    const response = await fetch(url);
    const bytes = await response.arrayBuffer();
    const ctx = new AudioContext();
    try {
      const decoded = await ctx.decodeAudioData(bytes.slice(0));
      const bounds = speechBounds(decoded.getChannelData(0), decoded.sampleRate);
      speechEndCache.set(url, bounds.end);
      return bounds.end;
    } finally {
      void ctx.close();
    }
  } catch {
    return null;
  }
}
