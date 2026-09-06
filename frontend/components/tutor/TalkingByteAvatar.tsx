"use client";

import { cn } from "@/lib/utils";
import { shouldBlink, visemeAt, VISEME_MOUTH, type Viseme } from "@/lib/viseme";

export function TalkingByteAvatar({
  speaking = false,
  narration = "",
  currentTime = 0,
  duration = 0,
  size = "lg",
  className,
}: {
  speaking?: boolean;
  narration?: string;
  currentTime?: number;
  duration?: number;
  size?: "sm" | "lg" | "xl";
  className?: string;
}) {
  const viseme = visemeAt(narration, currentTime, speaking, duration);
  const mouth = VISEME_MOUTH[viseme];
  const blink = shouldBlink(currentTime);
  const bob = speaking ? Math.sin(currentTime * 6) * 2.2 : 0;
  const dim =
    size === "xl" ? "h-[11.5rem] w-[8.75rem]" : size === "lg" ? "h-[8.25rem] w-[6.25rem]" : "h-16 w-12";

  return (
    <div className={cn("relative flex flex-col items-center", className)}>
      <svg
        viewBox="0 0 128 168"
        className={cn(dim, "overflow-visible drop-shadow-[0_12px_32px_rgba(34,211,238,0.42)]")}
        role="img"
        aria-label="Pavi talking"
        style={{ transform: `translateY(${bob}px)` }}
      >
        <ellipse cx="64" cy="160" rx="28" ry="6" fill="rgba(34,211,238,0.18)" />
        <circle cx="64" cy="12" r="6" fill={speaking ? "#67e8f9" : "#22d3ee"} />
        <rect x="62" y="16" width="4" height="14" rx="2" fill="#a1a1aa" />
        <rect x="22" y="48" width="12" height="22" rx="6" fill="#f59e0b" />
        <rect x="94" y="48" width="12" height="22" rx="6" fill="#f59e0b" />
        <rect x="28" y="28" width="72" height="68" rx="24" fill="#fbbf24" />
        <rect x="36" y="44" width="56" height="42" rx="14" fill="#0b1220" />
        {speaking ? <rect x="36" y="44" width="56" height="42" rx="14" fill="#22d3ee" opacity="0.18" /> : null}
        <rect x="44" y={blink ? 58 : 52} width="16" height={blink ? 2 : 9} rx="3" fill="#67e8f9" />
        <rect x="68" y={blink ? 58 : 52} width="16" height={blink ? 2 : 9} rx="3" fill="#67e8f9" />
        <Mouth viseme={viseme} mouth={mouth} />
        <path d="M38 94c8 8 18 12 26 12s18-4 26-12l14 54H24L38 94Z" fill="#27272a" />
        <path d="M50 108c8 6 20 6 28 0v44H50V108Z" fill="#3f3f46" />
        <circle cx="64" cy="132" r="11" fill="#fbbf24" />
        <path
          d="M59 136V128h4.2c3.4 0 5.4 1.5 5.4 4s-2 4-5.4 4H59Zm3.2-2.4h1c1.3 0 2.1-.6 2.1-1.6s-.8-1.6-2.1-1.6h-1v3.2Z"
          fill="#18181b"
        />
      </svg>
      <p
        className={cn(
          "mt-1 font-semibold uppercase tracking-[0.28em] text-cyan-100/90",
          size === "xl" ? "text-xs" : "text-[10px]",
        )}
      >
        Pavi
      </p>
    </div>
  );
}

function Mouth({ viseme, mouth }: { viseme: Viseme; mouth: { rx: number; ry: number; cy: number } }) {
  return (
    <g>
      <ellipse cx="64" cy={mouth.cy} rx={mouth.rx} ry={mouth.ry} fill="#7c2d12" />
      {viseme === "open" || viseme === "wide" ? (
        <ellipse cx="64" cy={mouth.cy + 1.2} rx={mouth.rx * 0.45} ry={mouth.ry * 0.35} fill="#fca5a5" />
      ) : null}
    </g>
  );
}
