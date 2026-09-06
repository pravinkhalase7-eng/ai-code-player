"use client";

import { cn } from "@/lib/utils";

export function ByteAvatar({
  speaking = false,
  size = "md",
  showName = true,
  className,
}: {
  speaking?: boolean;
  size?: "sm" | "md";
  showName?: boolean;
  className?: string;
}) {
          const px = size === "sm" ? "h-[4.5rem] w-14" : "h-28 w-20";
  return (
    <div className={cn("flex flex-col items-center", className)}>
      <div
        className={cn(
          "relative drop-shadow-[0_12px_24px_rgba(34,211,238,0.28)]",
          speaking && "animate-pulse",
        )}
      >
        <img
          src="/byte-avatar.svg"
          alt="Pavi"
          className={cn(px, "object-contain")}
        />
        {speaking ? (
          <span className="absolute -bottom-0.5 left-1/2 h-1.5 w-8 -translate-x-1/2 rounded-full bg-cyan-300/80" />
        ) : null}
      </div>
      {showName ? (
        <p className="mt-1 text-[10px] font-semibold uppercase tracking-[0.28em] text-amber-200/90">Pavi</p>
      ) : null}
    </div>
  );
}
