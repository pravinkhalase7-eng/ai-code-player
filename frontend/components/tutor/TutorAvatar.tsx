"use client";

import { motion } from "framer-motion";
import type { TutorExpression } from "@/types/lesson";
import { cn } from "@/lib/utils";

const EYES: Record<TutorExpression, [string, string]> = {
  idle: ["M18 22c2 3 6 3 8 0", "M38 22c2 3 6 3 8 0"],
  talking: ["M18 22c2 4 6 4 8 0", "M38 22c2 4 6 4 8 0"],
  thinking: ["M18 20c3 0 7 2 8 4", "M38 24c1-2 5-4 8-4"],
  happy: ["M18 24c2-3 6-3 8 0", "M38 24c2-3 6-3 8 0"],
  confused: ["M18 22c3 1 6-1 8 2", "M38 24c2-3 6 0 8-2"],
  pointing: ["M18 22c2 3 6 3 8 0", "M38 22c2 3 6 3 8 0"],
  explaining: ["M18 21c2 4 6 4 8 0", "M38 21c2 4 6 4 8 0"],
  celebrating: ["M18 24c2-4 6-4 8 0", "M38 24c2-4 6-4 8 0"],
  listening: ["M18 22c2 2 6 2 8 0", "M38 22c2 2 6 2 8 0"],
};

export function TutorAvatar({
  expression = "idle",
  speaking = false,
  gesture = "idle",
  className,
}: {
  expression?: TutorExpression;
  speaking?: boolean;
  gesture?: string;
  className?: string;
}) {
  const eyes = EYES[expression] ?? EYES.idle;
  return (
    <div className={cn("relative flex flex-col items-center", className)} data-gesture={gesture}>
      <motion.div
        animate={speaking ? { y: [0, -4, 0] } : { y: 0 }}
        transition={{ repeat: speaking ? Infinity : 0, duration: 0.7 }}
        className="relative"
      >
        <svg viewBox="0 0 72 72" className="h-28 w-28 drop-shadow-[0_12px_30px_rgba(251,191,36,0.35)]">
          <circle cx="36" cy="38" r="28" fill="#fbbf24" />
          <circle cx="24" cy="34" r="10" fill="#fff7ed" />
          <circle cx="48" cy="34" r="10" fill="#fff7ed" />
          <circle cx="24" cy="35" r="4" fill="#18181b" />
          <circle cx="48" cy="35" r="4" fill="#18181b" />
          <path d={eyes[0]} stroke="#18181b" strokeWidth="1.6" fill="none" />
          <path d={eyes[1]} stroke="#18181b" strokeWidth="1.6" fill="none" />
          <path d="M32 44c2 6 6 6 8 0" fill="#f97316" />
          <motion.ellipse
            cx="36"
            cy="52"
            rx="6"
            ry={speaking ? 3.4 : 1.6}
            fill="#7c2d12"
            animate={{ ry: speaking ? [1.5, 3.6, 1.5] : 1.6 }}
            transition={{ repeat: speaking ? Infinity : 0, duration: 0.28 }}
          />
          {gesture === "point_right" ? (
            <path d="M62 44c8 2 10 8 6 12" stroke="#f59e0b" strokeWidth="4" fill="none" strokeLinecap="round" />
          ) : null}
        </svg>
        {expression === "celebrating" ? (
          <div className="pointer-events-none absolute inset-0 animate-pulse rounded-full bg-amber-300/20" />
        ) : null}
      </motion.div>
      <p className="mt-2 text-xs font-medium uppercase tracking-[0.2em] text-amber-200/80">Pavi</p>
    </div>
  );
}
