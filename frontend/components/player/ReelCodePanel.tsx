"use client";

import { useLayoutEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import { syntaxClass, tokenizeLine } from "@/lib/codeSyntax";
import { formatResultChip, type ResultChip } from "@/lib/programRunner";
import type { HighlightRange } from "@/types/lesson";

export function ReelCodePanel({
  code,
  filename,
  highlight,
  caret = false,
  syntax = false,
  vivid = false,
  annotations = [],
}: {
  code: string;
  filename: string;
  highlight?: HighlightRange | null;
  caret?: boolean;
  syntax?: boolean;
  vivid?: boolean;
  annotations?: ResultChip[];
}) {
  const preRef = useRef<HTMLPreElement>(null);
  const lines = (code || " ").replace(/\n$/, "").split("\n");
  const chipByLine = new Map<number, ResultChip>();
  for (const chip of annotations) {
    if (!chipByLine.has(chip.line)) chipByLine.set(chip.line, chip);
  }

  useLayoutEffect(() => {
    const pre = preRef.current;
    if (!pre) return;
    let size = vivid ? (lines.length > 14 ? 22 : 26) : lines.length > 16 ? 13 : syntax ? 17 : 15;
    const floor = vivid ? 18 : 10;
    pre.style.fontSize = `${size}px`;
    pre.style.lineHeight = vivid ? "1.85" : syntax ? "1.65" : "1.5";
    pre.style.fontWeight = vivid ? "600" : "";
    while (size > floor && pre.scrollWidth > pre.clientWidth + 2) {
      size -= 0.25;
      pre.style.fontSize = `${size}px`;
    }
  }, [code, highlight, lines.length, syntax, vivid, annotations]);

  return (
    <div className="flex h-full min-h-0 flex-1 flex-col overflow-hidden">
      <div className="flex shrink-0 items-center gap-2 border-b border-white/10 bg-white/5 px-3 py-1.5">
        <span className="h-2 w-2 rounded-full bg-red-400/80" />
        <span className="h-2 w-2 rounded-full bg-amber-300/80" />
        <span className="h-2 w-2 rounded-full bg-emerald-400/80" />
        <span className="ml-1 truncate text-[11px] font-medium uppercase tracking-[0.14em] text-zinc-300">
          {filename}
        </span>
      </div>
      <pre
        ref={preRef}
        className={cn(
          "overflow-x-auto overflow-y-auto px-2 py-2 font-mono tracking-wide text-zinc-100",
          vivid && "px-3 py-3 text-white",
        )}
      >
        {lines.map((line, index) => {
          const lineNo = index + 1;
          const active = Boolean(
            highlight && lineNo >= highlight.start_line && lineNo <= highlight.end_line,
          );
          const chip = chipByLine.get(lineNo);
          const tokens = syntax ? tokenizeLine(line) : null;
          return (
            <div
              key={`${lineNo}-${line}`}
              ref={active ? (node) => node?.scrollIntoView({ block: "nearest" }) : undefined}
              className={cn(
                "grid gap-2 rounded-sm px-1",
                vivid ? "grid-cols-[3ch_minmax(0,1fr)]" : "grid-cols-[2.2ch_minmax(0,1fr)]",
                active && "bg-amber-400/25 outline outline-1 outline-amber-300/50",
              )}
            >
              <span className={cn("select-none text-right", vivid ? "text-zinc-400" : "text-zinc-600")}>{lineNo}</span>
              <span className="min-w-0 whitespace-pre">
                {tokens
                  ? tokens.map((token, tokenIndex) => (
                      <span key={`${tokenIndex}-${token.text}`} className={syntaxClass(token.kind, vivid)}>
                        {token.text}
                      </span>
                    ))
                  : line || " "}
                {caret && index === lines.length - 1 ? (
                  <span className="ml-px inline-block h-[1.05em] w-[0.55ch] translate-y-[0.12em] animate-pulse bg-lime-300 align-middle" />
                ) : null}
                {chip ? (
                  <span
                    className={cn(
                      "ml-3 inline-flex translate-y-[-1px] items-center rounded-md px-1.5 py-0.5 font-sans text-[12px] font-extrabold tracking-wide",
                      chip.kind === "ok" && "bg-emerald-400/20 text-emerald-300",
                      chip.kind === "bad" && "bg-rose-400/20 text-rose-300",
                      chip.kind === "out" && "bg-amber-400/20 text-amber-200",
                    )}
                  >
                    {formatResultChip(chip.text)}
                  </span>
                ) : null}
              </span>
            </div>
          );
        })}
      </pre>
    </div>
  );
}
