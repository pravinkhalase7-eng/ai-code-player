"use client";

import { ReelCodePanel } from "@/components/player/ReelCodePanel";
import { QUIZ_LETTERS, type TrickyQuizState } from "@/lib/trickyQuiz";
import { sourceFilename } from "@/lib/language";
import { cn } from "@/lib/utils";
import type { HighlightRange, Lesson } from "@/types/lesson";

export function TrickyQuizOverlay({
  lesson,
  state,
  highlight,
}: {
  lesson: Lesson;
  state: TrickyQuizState;
  highlight?: HighlightRange | null;
}) {
  const revealed = state.phase === "reveal";

  return (
    <div className="relative z-10 flex min-h-0 flex-1 flex-col justify-center gap-2 py-1">
      <p className="shrink-0 px-1 text-center text-[13px] font-semibold leading-5 text-zinc-100">
        {state.question}
      </p>
      <div className="relative flex min-h-0 flex-1 flex-col overflow-hidden rounded-2xl border border-white/12 bg-[#0b0d12]/96 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]">
        <ReelCodePanel
          code={state.code}
          filename={state.quiz.filename || sourceFilename(lesson.language)}
          highlight={highlight}
        />
        {state.phase === "countdown" ? (
          <div className="pointer-events-none absolute inset-0 z-20 flex items-center justify-center bg-black/25">
            <div className="quiz-timer" style={{ ["--quiz-ring" as string]: String(state.ring) }}>
              <svg viewBox="0 0 100 100" className="h-full w-full">
                <circle cx="50" cy="50" r="40" className="quiz-timer-track" />
                <circle cx="50" cy="50" r="40" className="quiz-timer-ring" />
              </svg>
              <span key={state.count} className="quiz-timer-count">
                {state.count}
              </span>
            </div>
          </div>
        ) : null}
      </div>
      <div className="grid shrink-0 grid-cols-1 gap-1.5">
        {state.options.map((option, index) => {
          const letter = QUIZ_LETTERS[index] || String(index + 1);
          const correct = revealed && index === state.answerIndex;
          const wrong = revealed && index !== state.answerIndex;
          return (
            <div
              key={`${letter}-${option}`}
              className={cn(
                "flex items-center gap-2 rounded-xl border px-3 py-2 text-left text-[13px] font-semibold leading-5",
                correct
                  ? "border-emerald-300/50 bg-emerald-400/20 text-emerald-50"
                  : wrong
                    ? "border-white/8 bg-white/4 text-zinc-500"
                    : "border-white/10 bg-white/6 text-zinc-100",
              )}
            >
              <span
                className={cn(
                  "inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[11px] font-extrabold",
                  correct ? "bg-emerald-400 text-zinc-950" : "bg-white/10 text-zinc-200",
                )}
              >
                {letter}
              </span>
              <span className="min-w-0 flex-1">{option}</span>
              {correct ? <span className="text-[11px] font-bold uppercase tracking-wide text-emerald-200">Answer</span> : null}
            </div>
          );
        })}
      </div>
    </div>
  );
}
