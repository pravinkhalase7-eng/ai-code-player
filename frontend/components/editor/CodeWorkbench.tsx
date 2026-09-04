"use client";

import Editor, { type OnMount } from "@monaco-editor/react";
import type { editor } from "monaco-editor";
import { FileCode2, FolderOpen } from "lucide-react";
import { useEffect, useMemo, useRef } from "react";
import { cn } from "@/lib/utils";
import type { HighlightRange } from "@/types/lesson";

const LANGUAGE_MAP: Record<string, string> = {
  java: "java",
  python: "python",
  javascript: "javascript",
  js: "javascript",
};

export function CodeWorkbench({
  code,
  language = "java",
  filename = "Main.java",
  highlight,
  onChange,
  readOnly = false,
  compact = false,
}: {
  code: string;
  language?: string;
  filename?: string;
  highlight?: HighlightRange | null;
  onChange?: (value: string) => void;
  readOnly?: boolean;
  compact?: boolean;
}) {
  const monacoLanguage = LANGUAGE_MAP[language] ?? "java";
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);
  const decorationIds = useRef<string[]>([]);

  const decorations = useMemo(() => {
    if (!highlight) return [];
    return [
      {
        range: {
          startLineNumber: highlight.start_line,
          startColumn: Math.max(1, highlight.start_col + 1),
          endLineNumber: highlight.end_line,
          endColumn: highlight.end_col ? highlight.end_col + 1 : 120,
        },
        options: {
          isWholeLine: true,
          className: "tutor-line-highlight",
          inlineClassName: "tutor-inline-highlight",
        },
      },
    ];
  }, [highlight]);

  const handleMount: OnMount = (mounted, monaco) => {
    editorRef.current = mounted;
    monaco.editor.defineTheme("tutor-dark", {
      base: "vs-dark",
      inherit: true,
      rules: [],
      colors: {
        "editor.background": "#0b1220",
        "editorLineNumber.foreground": "#64748b",
      },
    });
    monaco.editor.setTheme("tutor-dark");
    decorationIds.current = mounted.deltaDecorations([], decorations as never);
  };

  useEffect(() => {
    if (!editorRef.current) return;
    decorationIds.current = editorRef.current.deltaDecorations(
      decorationIds.current,
      decorations as never,
    );
    if (highlight) {
      editorRef.current.revealLineInCenter(highlight.start_line);
    }
  }, [decorations, highlight]);

  return (
    <div className={cn("flex h-full overflow-hidden rounded-2xl border border-white/10 bg-[#0b1220]", compact ? "min-h-0" : "min-h-[280px]")}>
      <aside className={cn("w-40 border-r border-white/10 bg-black/20 p-3 text-xs text-zinc-400", compact ? "hidden" : "hidden md:block")}>
        <div className="mb-2 flex items-center gap-2 font-semibold text-zinc-200">
          <FolderOpen className="h-3.5 w-3.5 text-amber-300" />
          Explorer
        </div>
        <div className="flex items-center gap-2 rounded-lg bg-amber-400/10 px-2 py-1.5 text-amber-100">
          <FileCode2 className="h-3.5 w-3.5" />
          {filename}
        </div>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <div className="flex border-b border-white/10 bg-white/5">
          <div className="border-r border-white/10 px-4 py-2 text-xs font-medium text-zinc-200">
            {filename}
          </div>
        </div>
        <div className={cn(compact ? "min-h-[220px] flex-1" : "min-h-[420px] flex-1", highlight && "tutor-has-highlight")}>
          <Editor
            value={code}
            language={monacoLanguage}
            theme="tutor-dark"
            onMount={handleMount}
            onChange={(value) => onChange?.(value ?? "")}
            options={{
              readOnly,
              minimap: { enabled: false },
              fontSize: 14,
              fontFamily: "var(--font-geist-mono), ui-monospace, monospace",
              lineNumbers: "on",
              scrollBeyondLastLine: false,
              automaticLayout: true,
              padding: { top: 12 },
              cursorBlinking: "smooth",
            }}
          />
        </div>
      </div>
    </div>
  );
}
