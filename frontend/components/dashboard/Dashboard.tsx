"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState, type MouseEvent } from "react";
import { ArrowRight, Clapperboard, Expand, GitBranch, ImageIcon, Info, RefreshCw, Sparkles, Timer, Trash2, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { createLesson, deleteAllLessons, deleteLesson, generateThumbnail, getHealth, listLessons } from "@/lib/api";
import { LANGUAGES, topicForLanguage, type LessonLanguage } from "@/lib/language";
import {
  SPOKEN_LANGUAGES,
  REEL_DURATIONS,
  readStoredFormat,
  readStoredReelSeconds,
  readStoredSpokenLanguage,
  storeFormat,
  storeReelSeconds,
  storeSpokenLanguage,
  type MakeMode,
  type ReelSeconds,
  type SpokenLanguage,
} from "@/lib/spokenLanguage";
import { cn } from "@/lib/utils";
import type { LessonSummary } from "@/types/lesson";

export function Dashboard() {
  const router = useRouter();
  const [topic, setTopic] = useState("Explain Java for loop");
  const [language, setLanguage] = useState<LessonLanguage>("java");
  const [spokenLanguage, setSpokenLanguage] = useState<SpokenLanguage>("en");
  const [format, setFormat] = useState<MakeMode>("lesson");
  const [reelSeconds, setReelSeconds] = useState<ReelSeconds>(30);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [deletingId, setDeletingId] = useState("");
  const [clearingAll, setClearingAll] = useState(false);
  const [thumbBusyId, setThumbBusyId] = useState("");
  const [previewThumb, setPreviewThumb] = useState<{ url: string; title: string } | null>(null);
  const [lessons, setLessons] = useState<LessonSummary[]>([]);
  const [health, setHealth] = useState<string>("");

  useEffect(() => {
    setSpokenLanguage(readStoredSpokenLanguage());
    setFormat(readStoredFormat());
    setReelSeconds(readStoredReelSeconds());
    const loadLessons = () =>
      void listLessons()
        .then((payload) => setLessons(payload.lessons))
        .catch(() => undefined);
    loadLessons();
    const onVis = () => {
      if (document.visibilityState === "visible") loadLessons();
    };
    document.addEventListener("visibilitychange", onVis);
    void getHealth()
      .then((payload) =>
        setHealth(
          payload.gemini_configured
            ? `${payload.gemini_model} • ${payload.google_tts_configured ? "Google Cloud TTS" : payload.tts_provider} • sandbox ${payload.code_runner}`
            : "Add GEMINI_API_KEY to generate lessons",
        ),
      )
      .catch(() => setHealth("Backend offline"));
    return () => document.removeEventListener("visibilitychange", onVis);
  }, []);


  async function removeLesson(lesson: LessonSummary, event: MouseEvent) {
    event.stopPropagation();
    event.preventDefault();
    const kind = lesson.format === "reel" ? "short" : "lesson";
    if (!window.confirm(`Delete this ${kind}?`)) return;
    setDeletingId(lesson.lesson_id);
    setError("");
    try {
      await deleteLesson(lesson.lesson_id);
      setLessons((current) => current.filter((item) => item.lesson_id !== lesson.lesson_id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not delete the lesson");
    } finally {
      setDeletingId("");
    }
  }

  async function clearAllLessons() {
    if (lessons.length === 0 || clearingAll) return;
    if (
      !window.confirm(
        `Delete all ${lessons.length} lesson${lessons.length === 1 ? "" : "s"}? This cannot be undone.`,
      )
    ) {
      return;
    }
    setClearingAll(true);
    setError("");
    try {
      await deleteAllLessons();
      setLessons([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not clear lessons");
    } finally {
      setClearingAll(false);
    }
  }

  async function regenThumbnail(lesson: LessonSummary, event: MouseEvent) {
    event.stopPropagation();
    event.preventDefault();
    if (thumbBusyId) return;
    setThumbBusyId(lesson.lesson_id);
    setError("");
    try {
      const payload = await generateThumbnail(lesson.lesson_id, true);
      const url = payload.lesson.thumbnail_url || "";
      setLessons((current) =>
        current.map((item) =>
          item.lesson_id === lesson.lesson_id ? { ...item, thumbnail_url: url } : item,
        ),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not regenerate thumbnail");
    } finally {
      setThumbBusyId("");
    }
  }

  function openThumbPreview(lesson: LessonSummary, event: MouseEvent) {
    event.stopPropagation();
    event.preventDefault();
    const url = lesson.thumbnail_url || "";
    if (!url) return;
    setPreviewThumb({
      url,
      title: lesson.format === "reel" ? lesson.topic : lesson.title,
    });
  }

  async function start() {
    setBusy(true);
    setError("");
    try {
      storeSpokenLanguage(spokenLanguage);
      storeFormat(format);
      const apiFormat = format === "lesson" ? "lesson" : "reel";
      if (apiFormat === "reel") storeReelSeconds(reelSeconds);
      const requiresCode =
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
      );
      router.push(`/learn/${created.lesson_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not start the lesson");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto flex min-h-dvh max-w-5xl flex-col justify-center gap-8 overflow-x-hidden px-4 py-6 sm:px-6 sm:py-10 md:gap-10 md:py-16">
      <div>
        <p className="text-sm uppercase tracking-[0.35em] text-amber-300/80">AI Coding Tutor</p>
        <h1 className="mt-3 max-w-3xl text-3xl font-semibold tracking-tight text-white sm:text-5xl md:text-6xl">
          A personal teacher sitting next to you, teaching programming visually.
        </h1>
        <p className="mt-4 max-w-2xl text-base text-zinc-400 sm:text-lg">
          Ask for a concept. Byte generates a lesson, types the code, runs it in a sandbox, and walks through every iteration.
          Or cut a catchy short — coding demos, or explain-only topics like "what is an LLM".
        </p>
      </div>

      <Card className="p-4 sm:p-6 md:p-8">
        <p className="mb-3 text-sm font-medium text-zinc-300">What do you want to learn?</p>
        <p className="mb-2 text-xs uppercase tracking-[0.2em] text-zinc-500">Code</p>
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
        <p className="mb-2 text-xs uppercase tracking-[0.2em] text-zinc-500">Teach in</p>
        <div className="mb-4 flex flex-wrap gap-2">
          {SPOKEN_LANGUAGES.map((item) => (
            <button
              key={item.id}
              type="button"
              aria-pressed={spokenLanguage === item.id}
              onClick={() => {
                setSpokenLanguage(item.id);
                storeSpokenLanguage(item.id);
              }}
              className={cn(
                "rounded-full border px-4 py-1.5 text-sm transition",
                spokenLanguage === item.id
                  ? "border-sky-300/60 bg-sky-400 text-zinc-950"
                  : "border-white/10 bg-white/5 text-zinc-300 hover:border-sky-300/30",
              )}
            >
              {item.label}
            </button>
          ))}
        </div>
        <p className="mb-4 text-xs text-zinc-500">
          Byte will teach in {SPOKEN_LANGUAGES.find((item) => item.id === spokenLanguage)?.label}.
        </p>
        <div className="mb-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
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
        {format === "reel" || format === "info" || format === "explainer" ? (
          <div className="mb-4">
            <p className="mb-2 flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-zinc-500">
              <Timer className="h-3.5 w-3.5" />
              Short length
            </p>
            <div className="flex flex-wrap gap-2">
              {REEL_DURATIONS.map((item) => (
                <button
                  key={item.seconds}
                  type="button"
                  aria-pressed={reelSeconds === item.seconds}
                  onClick={() => {
                    setReelSeconds(item.seconds);
                    storeReelSeconds(item.seconds);
                  }}
                  className={cn(
                    "rounded-full border px-4 py-1.5 text-sm transition",
                    reelSeconds === item.seconds
                      ? "border-amber-300/60 bg-amber-400 text-zinc-950"
                      : "border-white/10 bg-white/5 text-zinc-300 hover:border-amber-300/30",
                  )}
                >
                  {item.label}
                </button>
              ))}
            </div>
            <p className="mt-2 text-xs text-zinc-500">Byte will script and time the reel to about {reelSeconds} seconds.</p>
          </div>
        ) : null}
        <div className="flex flex-col gap-3 sm:flex-row">
          <Input value={topic} onChange={(event) => setTopic(event.target.value)} />
          <Button onClick={start} disabled={busy} className="min-h-11 w-full sm:w-48">
            {busy ? "Preparing..." : format === "explainer" ? "Make Explainer" : format === "info" ? "Make Info Reel" : format === "reel" ? "Make a Short" : "Start Learning"}
            <ArrowRight className="h-4 w-4" />
          </Button>
        </div>
        {error ? <p className="mt-3 text-sm text-red-300">{error}</p> : null}
        {health ? <p className="mt-3 text-xs text-zinc-500">{health}</p> : null}
      </Card>

      <section>
        <div className="mb-4 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-zinc-300">
            <Sparkles className="h-4 w-4 text-amber-300" />
            Continue Learning
          </div>
          {lessons.length > 0 ? (
            <button
              type="button"
              onClick={() => void clearAllLessons()}
              disabled={clearingAll || Boolean(deletingId)}
              className="inline-flex items-center gap-1.5 rounded-full border border-red-300/30 bg-red-500/10 px-3 py-1.5 text-xs font-semibold text-red-200 transition hover:border-red-300/50 hover:bg-red-500/20 disabled:opacity-50"
            >
              <Trash2 className="h-3.5 w-3.5" />
              {clearingAll ? "Clearing..." : "Clear all"}
            </button>
          ) : null}
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {lessons.length === 0 ? (
            <Card className="p-5 text-sm text-zinc-400">Your next lesson will appear here.</Card>
          ) : (
            lessons.map((lesson) => {
              const done = lesson.completion_percent >= 99;
              const scene = Math.max(1, (lesson.scene_index ?? 0) + 1);
              const deleting = deletingId === lesson.lesson_id;
              return (
                <div key={lesson.lesson_id} className="relative w-full">
                  <button
                    type="button"
                    onClick={() => router.push(`/learn/${lesson.lesson_id}`)}
                    className="w-full text-left"
                    disabled={deleting}
                  >
                    <Card className="overflow-hidden p-0 transition hover:border-amber-300/30">
                      {lesson.format === "reel" && lesson.thumbnail_url ? (
                        <div className="relative h-36 w-full overflow-hidden bg-zinc-900 sm:h-44">
                          <img src={lesson.thumbnail_url} alt="" className="h-full w-full object-cover" />
                          <span className="absolute left-3 top-3 rounded-full bg-amber-400 px-2 py-0.5 text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-950">
                            {lesson.reel_seconds ? `${lesson.reel_seconds}s` : "Short"}
                          </span>
                        </div>
                      ) : lesson.format === "reel" ? (
                        <div className="relative flex h-28 w-full items-center justify-center bg-zinc-900/80 sm:h-32">
                          <span className="text-xs text-zinc-500">No thumbnail yet</span>
                        </div>
                      ) : null}
                      <div className="p-4 sm:p-5">
                        <div className="flex items-start justify-between gap-3 pr-10">
                          <p className="min-w-0 flex-1 font-semibold text-white">
                            {lesson.format === "reel" ? lesson.topic : lesson.title}
                          </p>
                          <span className="shrink-0 text-xs uppercase text-amber-200">
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
                      </div>
                    </Card>
                  </button>
                  {lesson.format === "reel" ? (
                    <div className="absolute bottom-[7.5rem] right-2 z-10 flex gap-1.5 sm:bottom-[8.5rem]">
                      {lesson.thumbnail_url ? (
                        <button
                          type="button"
                          title="View thumbnail fullscreen"
                          aria-label="View thumbnail fullscreen"
                          className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-white/20 bg-zinc-950/80 text-white shadow-lg backdrop-blur hover:border-cyan-300/50 hover:bg-cyan-500/20"
                          onClick={(event) => openThumbPreview(lesson, event)}
                        >
                          <Expand className="h-4 w-4" />
                        </button>
                      ) : null}
                      <button
                        type="button"
                        title="Regenerate thumbnail"
                        aria-label="Regenerate thumbnail"
                        disabled={thumbBusyId === lesson.lesson_id}
                        className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-white/20 bg-zinc-950/80 text-white shadow-lg backdrop-blur hover:border-amber-300/50 hover:bg-amber-500/20 disabled:opacity-50"
                        onClick={(event) => void regenThumbnail(lesson, event)}
                      >
                        {lesson.thumbnail_url ? (
                          <RefreshCw className={`h-4 w-4 ${thumbBusyId === lesson.lesson_id ? "animate-spin" : ""}`} />
                        ) : (
                          <ImageIcon className={`h-4 w-4 ${thumbBusyId === lesson.lesson_id ? "animate-spin" : ""}`} />
                        )}
                      </button>
                    </div>
                  ) : null}
                  <button
                    type="button"
                    aria-label={lesson.format === "reel" ? "Delete this short" : "Delete this lesson"}
                    title={lesson.format === "reel" ? "Delete this short" : "Delete this lesson"}
                    disabled={deleting}
                    onClick={(event) => void removeLesson(lesson, event)}
                    className="absolute right-2 top-2 z-10 inline-flex h-11 w-11 items-center justify-center rounded-full border border-white/15 bg-zinc-950/80 text-zinc-200 shadow-lg backdrop-blur transition hover:border-red-300/50 hover:bg-red-500/20 hover:text-red-100 disabled:opacity-50"
                  >
                    <Trash2 className="h-5 w-5" strokeWidth={2.25} />
                  </button>
                </div>
              );
            })
          )}
        </div>
      </section>

      {previewThumb ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 p-4 backdrop-blur-sm"
          role="dialog"
          aria-modal="true"
          aria-label="Thumbnail preview"
          onClick={() => setPreviewThumb(null)}
        >
          <button
            type="button"
            className="absolute right-4 top-4 inline-flex h-11 w-11 items-center justify-center rounded-full border border-white/20 bg-zinc-950/80 text-white"
            aria-label="Close preview"
            onClick={() => setPreviewThumb(null)}
          >
            <X className="h-5 w-5" />
          </button>
          <div
            className="relative max-h-[92vh] w-full max-w-md overflow-hidden rounded-2xl border border-white/15 bg-zinc-950 shadow-2xl"
            onClick={(event) => event.stopPropagation()}
          >
            <img src={previewThumb.url} alt={previewThumb.title} className="h-auto w-full object-contain" />
            <p className="border-t border-white/10 px-4 py-3 text-sm font-semibold text-zinc-100">{previewThumb.title}</p>
          </div>
        </div>
      ) : null}
    </div>
  );
}
