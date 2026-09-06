"use client";

import { useLayoutEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import type { HighlightRange } from "@/types/lesson";

export function ReelCodePanel({
  code,
  filename,
  highlight,
}: {
  code: string;
  filename: string;
  highlight?: HighlightRange | null;
}) {
  const preRef = useRef<HTMLPreElement>(null);
  const lines = (code || " ").replace(/\n$/, "").split("\n");

  useLayoutEffect(() => {
    const pre = preRef.current;
    if (!pre) return;
    let size = lines.length > 16 ? 13 : 15;
    pre.style.fontSize = `${size}px`;
    pre.style.lineHeight = "1.5";
    while (size > 10 && pre.scrollWidth > pre.clientWidth + 2) {
      size -= 0.25;
      pre.style.fontSize = `${size}px`;
    }
  }, [code, highlight, lines.length]);

  return (
    <div className="flex min-h-0 flex-col overflow-hidden">
      <div className="flex shrink-0 items-center gap-2 border-b border-white/10 bg-white/5 px-3 py-1.5">
        <span className="h-2 w-2 rounded-full bg-red-400/80" />
        <span className="h-2 w-2 rounded-full bg-amber-300/80" />
        <span className="h-2 w-2 rounded-full bg-emerald-400/80" />
        <span className="ml-1 truncate text-[11px] font-medium uppercase tracking-[0.14em] text-zinc-300">
          {filename}
        </span>
      </div>
      <pre ref={preRef} className="overflow-x-auto overflow-y-auto px-2 py-2 font-mono text-zinc-100">
        {lines.map((line, index) => {
          const lineNo = index + 1;
          const active = Boolean(
            highlight && lineNo >= highlight.start_line && lineNo <= highlight.end_line,
          );
          return (
            <div
              key={`${lineNo}-${line}`}
              ref={active ? (node) => node?.scrollIntoView({ block: "nearest" }) : undefined}
              className={cn(
                "grid grid-cols-[2.2ch_minmax(0,1fr)] gap-2 rounded-sm px-1",
                active && "bg-amber-400/25 outline outline-1 outline-amber-300/50",
              )}
            >
              <span className="select-none text-right text-zinc-600">{lineNo}</span>
              <span className="min-w-0 whitespace-pre">{line || " "}</span>
            </div>
          );
        })}
      </pre>
    </div>
  );
}
