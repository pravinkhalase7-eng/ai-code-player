"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

export function Terminal({
  command,
  lines,
  stderr,
  success = true,
  className,
}: {
  command?: string;
  lines: string[];
  stderr?: string;
  success?: boolean;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "overflow-hidden rounded-2xl border border-white/10 bg-zinc-950 font-mono text-sm",
        className,
      )}
    >
      <div className="flex items-center gap-2 border-b border-white/10 bg-white/5 px-4 py-2 text-xs text-zinc-400">
        <span className="h-2.5 w-2.5 rounded-full bg-red-400/80" />
        <span className="h-2.5 w-2.5 rounded-full bg-amber-300/80" />
        <span className="h-2.5 w-2.5 rounded-full bg-emerald-400/80" />
        <span className="ml-2">Terminal</span>
      </div>
      <div className="max-h-40 space-y-1 overflow-auto p-4 text-zinc-200">
        {command ? <p className="text-amber-200">$ {command}</p> : null}
        {lines.map((line, index) => (
          <motion.p
            key={`${line}-${index}`}
            initial={{ opacity: 0, x: 8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.12, duration: 0.2 }}
          >
            <span className="text-zinc-500">&gt; </span>
            {line}
          </motion.p>
        ))}
        {stderr ? (
          <p className={success ? "text-zinc-400" : "text-red-300"}>{stderr}</p>
        ) : null}
      </div>
    </div>
  );
}
