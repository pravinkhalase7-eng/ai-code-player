"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { LessonPlayer } from "@/components/player/LessonPlayer";
import { Button } from "@/components/ui/button";
import { createLesson, getLesson, getProgress } from "@/lib/api";
import { SPOKEN_LANGUAGES } from "@/lib/spokenLanguage";
import type { Lesson } from "@/types/lesson";

const STATUS_COPY: Record<string, string> = {
  queued: "Byte is starting your visual lesson…",
  running: "Byte is writing the walkthrough and recording a natural voice…",
};

const REEL_STATUS_COPY: Record<string, string> = {
  queued: "Byte is lining up a short…",
  running: "Byte is cutting a catchy reel and recording the voice…",
};

export function LearnClient({ lessonId }: { lessonId: string }) {
  const router = useRouter();
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [status, setStatus] = useState("queued");
  const [warnings, setWarnings] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [elapsed, setElapsed] = useState(0);
  const [retrying, setRetrying] = useState(false);
  const [progressIndex, setProgressIndex] = useState<number | null>(null);
  const progressLoaded = useRef(false);

  useEffect(() => {
    const started = Date.now();
    const tick = window.setInterval(() => setElapsed(Math.floor((Date.now() - started) / 1000)), 1000);
    return () => window.clearInterval(tick);
  }, [lessonId]);

  useEffect(() => {
    let cancelled = false;
    const begun = Date.now();
    progressLoaded.current = false;
    setProgressIndex(null);
    async function poll() {
      try {
        const payload = await getLesson(lessonId);
        if (cancelled) return;
        setLesson((current) => {
          const next = payload.lesson;
          if (
            current &&
            current.lesson_id === next.lesson_id &&
            current.thumbnail_url === next.thumbnail_url &&
            current.thumbnail_custom === next.thumbnail_custom &&
            current.scenes.map((scene) => scene.audio_url).join() === next.scenes.map((scene) => scene.audio_url).join()
          ) {
            return current;
          }
          return next;
        });
        setStatus(payload.status);
        setWarnings(payload.warnings);
        if (payload.status === "failed") {
          setError(payload.warnings[0] || "The tutor could not build this lesson. Try again.");
          return;
        }
        if (payload.status !== "ready") {
          window.setTimeout(poll, 1500);
          return;
        }
        if (!progressLoaded.current) {
          progressLoaded.current = true;
          try {
            const progress = await getProgress(lessonId);
            if (!cancelled) {
              const startAt =
                progress.completion_percent >= 99
                  ? 0
                  : Math.max(0, progress.scene_index || 0);
              setProgressIndex(startAt);
            }
          } catch {
            if (!cancelled) setProgressIndex(0);
          }
        }
        const missingAudio = payload.lesson.scenes.some((item) => !item.audio_url);
        if (missingAudio || Date.now() - begun < 120000) {
          window.setTimeout(poll, 2000);
        }
      } catch {
        if (cancelled) return;
        if (Date.now() - begun < 120000) {
          window.setTimeout(poll, 2000);
          return;
        }
        setError("Could not reach the tutor API. Check that it is running, then try again.");
      }
    }
    void poll();
    return () => {
      cancelled = true;
    };
  }, [lessonId]);

  async function retry() {
    const topic = lesson?.topic || "Java for loop";
    setRetrying(true);
    setError("");
    try {
      const created = await createLesson(
        topic,
        lesson?.language || "java",
        lesson?.level || "beginner",
        lesson?.format || "lesson",
        lesson?.spoken_language || "en",
        lesson?.reel_seconds || 30,
      );
      router.replace(`/learn/${created.lesson_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not start a new lesson");
      setRetrying(false);
    }
  }

  if (error) {
    return (
      <div className="mx-auto max-w-xl py-24 text-center">
        <p className="text-lg text-red-300">{error}</p>
        <div className="mt-6 flex justify-center gap-4">
          <Button onClick={() => void retry()} disabled={retrying}>
            {retrying ? "Starting…" : "Try again"}
          </Button>
          <Link href="/" className="inline-flex items-center text-amber-300">
            Back home
          </Link>
        </div>
      </div>
    );
  }

  if (!lesson || status !== "ready" || progressIndex === null) {
    return (
      <div className="flex min-h-[70vh] flex-col items-center justify-center gap-4 px-6 text-center">
        <div className="h-16 w-16 animate-spin rounded-full border-4 border-amber-300/20 border-t-amber-300" />
        <p className="text-zinc-300">
          {(lesson?.format === "reel" ? REEL_STATUS_COPY[status] : STATUS_COPY[status]) ??
            (lesson?.format === "reel"
              ? "Byte is cutting your short…"
              : "Byte is preparing your visual lesson…")}
        </p>
        {lesson?.spoken_language && lesson.spoken_language !== "en" ? (
          <p className="text-sm text-sky-200">
            Teaching in {SPOKEN_LANGUAGES.find((item) => item.id === lesson.spoken_language)?.label || lesson.spoken_language}
          </p>
        ) : null}
        <p className="text-xs uppercase tracking-[0.3em] text-zinc-500">
          {status}
          {elapsed > 0 ? ` · ${elapsed}s` : ""}
        </p>
        {elapsed >= 90 ? (
          <div className="mt-4 space-y-3">
            <p className="max-w-md text-sm text-zinc-400">
              This is taking longer than usual. You can wait, or start a fresh lesson.
            </p>
            <Button onClick={() => void retry()} disabled={retrying}>
              {retrying ? "Starting…" : "Start a new lesson"}
            </Button>
          </div>
        ) : null}
      </div>
    );
  }

  return <LessonPlayer lesson={lesson} warnings={warnings} initialSceneIndex={progressIndex} onLessonChange={setLesson} />;
}
