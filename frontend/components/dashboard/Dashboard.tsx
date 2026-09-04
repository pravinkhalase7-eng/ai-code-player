"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ArrowRight, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { createLesson, getHealth, listLessons } from "@/lib/api";
import { LANGUAGES, topicForLanguage, type LessonLanguage } from "@/lib/language";
import { cn } from "@/lib/utils";
import type { LessonSummary } from "@/types/lesson";

export function Dashboard() {
  const router = useRouter();
  const [topic, setTopic] = useState("Explain Java for loop");
  const [language, setLanguage] = useState<LessonLanguage>("java");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [lessons, setLessons] = useState<LessonSummary[]>([]);
  const [health, setHealth] = useState<string>("");

  useEffect(() => {
    void listLessons()
      .then((payload) => setLessons(payload.lessons))
      .catch(() => undefined);
    void getHealth()
      .then((payload) =>
        setHealth(
          payload.gemini_configured
            ? `${payload.gemini_model} • ${payload.google_tts_configured ? "Google Cloud TTS" : payload.tts_provider} • sandbox ${payload.code_runner}`
            : "Add GEMINI_API_KEY to generate lessons",
        ),
      )
      .catch(() => setHealth("Backend offline"));
  }, []);

  async function start() {
    setBusy(true);
    setError("");
    try {
      const created = await createLesson(topic || "for loop", language, "beginner");
      router.push(`/learn/${created.lesson_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not start the lesson");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-5xl flex-col justify-center gap-10 px-6 py-16">
      <div>
        <p className="text-sm uppercase tracking-[0.35em] text-amber-300/80">AI Coding Tutor</p>
        <h1 className="mt-3 max-w-3xl text-5xl font-semibold tracking-tight text-white md:text-6xl">
          A personal teacher sitting next to you, teaching programming visually.
        </h1>
        <p className="mt-4 max-w-2xl text-lg text-zinc-400">
          Ask for a concept. Byte generates a lesson, types the code, runs it in a sandbox, and walks through every iteration.
        </p>
      </div>

      <Card className="p-6 md:p-8">
        <p className="mb-3 text-sm font-medium text-zinc-300">What do you want to learn?</p>
        <div className="mb-4 flex flex-wrap gap-2">
          {LANGUAGES.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => {
                setLanguage(item.id);
                setTopic((current) => topicForLanguage(item.id, current));
              }}
              className={cn(
                "rounded-full border px-4 py-1.5 text-sm transition",
                language === item.id
                  ? "border-amber-300/60 bg-amber-400 text-zinc-950"
                  : "border-white/10 bg-white/5 text-zinc-300 hover:border-amber-300/30",
              )}
            >
              {item.label}
            </button>
          ))}
        </div>
        <div className="flex flex-col gap-3 md:flex-row">
          <Input value={topic} onChange={(event) => setTopic(event.target.value)} />
          <Button onClick={start} disabled={busy} className="md:w-48">
            {busy ? "Preparing..." : "Start Learning"}
            <ArrowRight className="h-4 w-4" />
          </Button>
        </div>
        {error ? <p className="mt-3 text-sm text-red-300">{error}</p> : null}
        {health ? <p className="mt-3 text-xs text-zinc-500">{health}</p> : null}
      </Card>

      <section>
        <div className="mb-4 flex items-center gap-2 text-zinc-300">
          <Sparkles className="h-4 w-4 text-amber-300" />
          Continue Learning
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          {lessons.length === 0 ? (
            <Card className="p-5 text-sm text-zinc-400">Your next lesson will appear here.</Card>
          ) : (
            lessons.map((lesson) => {
              const done = lesson.completion_percent >= 99;
              const scene = Math.max(1, (lesson.scene_index ?? 0) + 1);
              return (
                <button
                  key={lesson.lesson_id}
                  type="button"
                  onClick={() => router.push(`/learn/${lesson.lesson_id}`)}
                  className="text-left"
                >
                  <Card className="p-5 transition hover:border-amber-300/30">
                    <div className="flex items-center justify-between gap-3">
                      <p className="font-semibold text-white">{lesson.title}</p>
                      <span className="text-xs uppercase text-amber-200">
                        {lesson.status === "ready" ? lesson.language : lesson.status}
                      </span>
                    </div>
                    <div className="mt-4 h-2 overflow-hidden rounded-full bg-white/10">
                      <div
                        className="h-full rounded-full bg-amber-400"
                        style={{ width: `${Math.max(8, lesson.completion_percent)}%` }}
                      />
                    </div>
                    <p className="mt-2 text-xs text-zinc-400">
                      {done
                        ? "Completed — open to review"
                        : lesson.completion_percent > 0
                          ? `Resume at scene ${scene} · ${Math.round(lesson.completion_percent)}%`
                          : "Start this lesson"}
                    </p>
                  </Card>
                </button>
              );
            })
          )}
        </div>
      </section>
    </div>
  );
}
