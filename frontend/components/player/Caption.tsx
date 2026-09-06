"use client";

import { useMemo } from "react";
import {
  activeWordIndex,
  buildKaraokeWords,
  karaokeWindow,
} from "@/lib/karaokeCaption";
import { cn } from "@/lib/utils";

type SegmentLike = { text?: string; start: number; end: number };

export function Caption({ text }: { text: string }) {
  if (!text) return null;
  return (
    <div className="pointer-events-none absolute inset-x-0 bottom-4 mx-auto max-w-3xl px-4">
      <p className="rounded-2xl bg-black/70 px-4 py-2 text-center text-sm text-white shadow-lg">{text}</p>
    </div>
  );
}

/** Audio-synced word highlight for the current spoken cue. */
export function KaraokeCaption({
  text,
  currentTime,
  duration,
  cueStart,
  cueEnd,
  segments,
  className,
}: {
  text: string;
  currentTime: number;
  duration: number;
  cueStart?: number;
  cueEnd?: number;
  segments?: SegmentLike[] | null;
  className?: string;
}) {
  const words = useMemo(
    () =>
      buildKaraokeWords(text, duration, {
        cueStart,
        cueEnd,
        segments,
      }),
    [text, duration, cueStart, cueEnd, segments],
  );
  const active = activeWordIndex(words, currentTime);
  const windowWords = karaokeWindow(words, Math.max(0, active), 12);

  if (!text.trim()) return null;

  return (
    <div
      className={cn(
        "karaoke-caption min-w-0 flex-1 rounded-2xl border border-white/15 bg-black/70 px-3.5 py-3 shadow-[0_12px_40px_rgba(0,0,0,0.45)] backdrop-blur-md",
        className,
      )}
    >
      <p className="flex flex-wrap content-center gap-x-1.5 gap-y-1 text-[15px] font-semibold leading-6 tracking-tight text-zinc-300 sm:text-base">
        {windowWords.length ? (
          windowWords.map((word) => {
            const isActive = word.index === active;
            const isPast = word.index < active;
            return (
              <span
                key={`${word.index}-${word.text}`}
                className={cn(
                  "karaoke-word inline-block transition-all duration-100",
                  isActive && "karaoke-word-active",
                  isPast && !isActive && "text-white",
                  !isPast && !isActive && "text-zinc-500",
                )}
              >
                {word.text}
              </span>
            );
          })
        ) : (
          <span className="text-white">{text}</span>
        )}
      </p>
    </div>
  );
}
