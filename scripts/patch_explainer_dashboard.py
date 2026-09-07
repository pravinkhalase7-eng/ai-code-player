#!/usr/bin/env python3
"""Add Explainer card to Dashboard."""
from pathlib import Path

ROOT = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder")
path = ROOT / "frontend/components/dashboard/Dashboard.tsx"
text = path.read_text(encoding="utf-8")

text = text.replace(
    'import { ArrowRight, Clapperboard, Info, Sparkles, Timer, Trash2 } from "lucide-react";',
    'import { ArrowRight, Clapperboard, GitBranch, Info, Sparkles, Timer, Trash2 } from "lucide-react";',
    1,
)

# start() logic
old_start = '''      const requiresCode = format === "info" ? false : format === "reel" ? true : undefined;
      const created = await createLesson(
        topic || (format === "info" ? "what is large language model" : "for loop"),
        language,
        "beginner",
        apiFormat,
        spokenLanguage,
        reelSeconds,
        requiresCode,
      );'''
new_start = '''      const requiresCode =
        format === "info" || format === "explainer" ? false : format === "reel" ? true : undefined;
      const reelMode =
        format === "explainer" ? "explainer" : format === "info" ? "info" : format === "reel" ? "code" : undefined;
      const defaultTopic =
        format === "explainer"
          ? "how hashmap works in java"
          : format === "info"
            ? "what is large language model"
            : "for loop";
      const created = await createLesson(
        topic || defaultTopic,
        language,
        "beginner",
        apiFormat,
        spokenLanguage,
        reelSeconds,
        requiresCode,
        reelMode,
      );'''
if old_start not in text:
    raise SystemExit("start() block missing")
text = text.replace(old_start, new_start, 1)

# mode cards grid
old_cards = '''        <div className="mb-4 grid gap-2 sm:grid-cols-3">
          {(
            [
              { id: "lesson" as const, label: "Full lesson", hint: "Walkthrough, execution, quiz" },
              { id: "reel" as const, label: "Code short", hint: "Hook + runnable program" },
              { id: "info" as const, label: "Info reel", hint: "No program — concepts like LLMs" },
            ] as const
          ).map((item) => (
            <button
              key={item.id}
              type="button"
              aria-pressed={format === item.id}
              onClick={() => {
                setFormat(item.id);
                storeFormat(item.id);
                if (item.id === "info" && (!topic.trim() || /for loop/i.test(topic))) {
                  setTopic("what is large language model");
                }
              }}
              className={cn(
                "rounded-2xl border px-4 py-3 text-left transition",
                format === item.id
                  ? item.id === "info"
                    ? "border-violet-300/60 bg-violet-400/15 text-white"
                    : "border-amber-300/60 bg-amber-400/15 text-white"
                  : "border-white/10 bg-white/5 text-zinc-300 hover:border-amber-300/30",
              )}
            >
              <span className="flex items-center gap-2 text-sm font-semibold">
                {item.id === "reel" ? (
                  <Clapperboard className="h-4 w-4 text-amber-300" />
                ) : item.id === "info" ? (
                  <Info className="h-4 w-4 text-violet-300" />
                ) : (
                  <Sparkles className="h-4 w-4 text-amber-300" />
                )}
                {item.label}
              </span>
              <span className="mt-1 block text-xs text-zinc-400">{item.hint}</span>
            </button>
          ))}
        </div>
        {format === "reel" || format === "info" ? ('''

new_cards = '''        <div className="mb-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
          {(
            [
              { id: "lesson" as const, label: "Full lesson", hint: "Walkthrough, execution, quiz" },
              { id: "reel" as const, label: "Code short", hint: "Hook + runnable program" },
              { id: "info" as const, label: "Info reel", hint: "No program — concepts like LLMs" },
              { id: "explainer" as const, label: "Explainer", hint: "Diagrams + how it works" },
            ] as const
          ).map((item) => (
            <button
              key={item.id}
              type="button"
              aria-pressed={format === item.id}
              onClick={() => {
                setFormat(item.id);
                storeFormat(item.id);
                if (item.id === "info" && (!topic.trim() || /for loop/i.test(topic))) {
                  setTopic("what is large language model");
                }
                if (item.id === "explainer" && (!topic.trim() || /for loop/i.test(topic))) {
                  setTopic("how hashmap works in java");
                }
              }}
              className={cn(
                "rounded-2xl border px-4 py-3 text-left transition",
                format === item.id
                  ? item.id === "info"
                    ? "border-violet-300/60 bg-violet-400/15 text-white"
                    : item.id === "explainer"
                      ? "border-cyan-300/60 bg-cyan-400/15 text-white"
                      : "border-amber-300/60 bg-amber-400/15 text-white"
                  : "border-white/10 bg-white/5 text-zinc-300 hover:border-amber-300/30",
              )}
            >
              <span className="flex items-center gap-2 text-sm font-semibold">
                {item.id === "reel" ? (
                  <Clapperboard className="h-4 w-4 text-amber-300" />
                ) : item.id === "info" ? (
                  <Info className="h-4 w-4 text-violet-300" />
                ) : item.id === "explainer" ? (
                  <GitBranch className="h-4 w-4 text-cyan-300" />
                ) : (
                  <Sparkles className="h-4 w-4 text-amber-300" />
                )}
                {item.label}
              </span>
              <span className="mt-1 block text-xs text-zinc-400">{item.hint}</span>
            </button>
          ))}
        </div>
        {format === "reel" || format === "info" || format === "explainer" ? ('''

if old_cards not in text:
    raise SystemExit("cards block missing")
text = text.replace(old_cards, new_cards, 1)

# Button label
text = text.replace(
    '{busy ? "Preparing..." : format === "info" ? "Make Info Reel" : format === "reel" ? "Make a Short" : "Start Learning"}',
    '{busy ? "Preparing..." : format === "explainer" ? "Make Explainer" : format === "info" ? "Make Info Reel" : format === "reel" ? "Make a Short" : "Start Learning"}',
    1,
)

# List badge for explainer
old_badge = '''                          <span className="shrink-0 text-xs uppercase text-amber-200">
                            {lesson.format === "reel"
                              ? `${lesson.reel_seconds || 30}s short`
                              : lesson.status === "ready"
                                ? lesson.language
                                : lesson.status}
                            {lesson.spoken_language && lesson.spoken_language !== "en"
                              ? ` · ${lesson.spoken_language}`
                              : ""}
                          </span>'''
new_badge = '''                          <span className="shrink-0 text-xs uppercase text-amber-200">
                            {lesson.format === "reel"
                              ? lesson.reel_mode === "explainer"
                                ? `${lesson.reel_seconds || 30}s Explainer`
                                : lesson.reel_mode === "info" || lesson.requires_code === false
                                  ? `${lesson.reel_seconds || 30}s Info`
                                  : `${lesson.reel_seconds || 30}s short`
                              : lesson.status === "ready"
                                ? lesson.language
                                : lesson.status}
                            {lesson.spoken_language && lesson.spoken_language !== "en"
                              ? ` · ${lesson.spoken_language}`
                              : ""}
                          </span>'''
if old_badge not in text:
    raise SystemExit("badge missing")
text = text.replace(old_badge, new_badge, 1)

path.write_text(text, encoding="utf-8")
print("Dashboard ok")
