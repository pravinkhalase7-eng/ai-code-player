"use client";

import { Pause, Play, RotateCcw, SkipBack, SkipForward } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { LessonScene } from "@/types/lesson";

const RATES = [0.5, 0.75, 1, 1.25, 1.5, 1.75];

function formatTime(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds < 0) return "0:00";
  const whole = Math.floor(seconds);
  const minutes = Math.floor(whole / 60);
  const rest = whole % 60;
  return `${minutes}:${rest.toString().padStart(2, "0")}`;
}

function sceneLength(scene: LessonScene, liveDuration?: number): number {
  if (typeof liveDuration === "number" && Number.isFinite(liveDuration) && liveDuration > 0.4) {
    return liveDuration;
  }
  return Math.max(3, scene.duration || 8);
}

export function PlayerTransport({
  scenes,
  index,
  currentTime,
  duration,
  playing,
  rate,
  onPlayPause,
  onRate,
  onSeekScene,
  onSeekLesson,
  onPrev,
  onNext,
  onReplay,
  compact = false,
}: {
  scenes: LessonScene[];
  index: number;
  currentTime: number;
  duration: number;
  playing: boolean;
  rate: number;
  onPlayPause: () => void;
  onRate: (value: number) => void;
  onSeekScene: (time: number) => void;
  onSeekLesson: (time: number) => void;
  onPrev: () => void;
  onNext: () => void;
  onReplay: () => void;
  compact?: boolean;
}) {
  const lengths = scenes.map((scene, sceneIndex) =>
    sceneLength(scene, sceneIndex === index ? duration : undefined),
  );
  const lessonTotal = lengths.reduce((sum, value) => sum + value, 0) || 1;
  const elapsedBefore = lengths.slice(0, index).reduce((sum, value) => sum + value, 0);
  const lessonTime = elapsedBefore + Math.min(currentTime, lengths[index] || 0);
  const sceneProgress = duration > 0 ? Math.min(100, (currentTime / duration) * 100) : 0;
  const lessonProgress = (lessonTime / lessonTotal) * 100;

  return (
    <div className={cn("rounded-2xl border border-white/10 bg-zinc-950/70", compact ? "p-2.5" : "p-4")}>
      <div className={cn("flex flex-wrap items-center gap-2", compact ? "mb-2" : "mb-3")}>
        <Button variant="ghost" size="icon" onClick={onPrev} aria-label="Previous scene">
          <SkipBack className="h-4 w-4" />
        </Button>
        <Button variant="ghost" size="icon" onClick={onPlayPause} aria-label={playing ? "Pause" : "Play"}>
          {playing ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
        </Button>
        <Button variant="ghost" size="icon" onClick={onNext} aria-label="Next scene">
          <SkipForward className="h-4 w-4" />
        </Button>
        <Button variant="ghost" size="sm" onClick={onReplay}>
          <RotateCcw className="h-4 w-4" /> Replay
        </Button>
        <p className="ml-auto text-xs tabular-nums text-zinc-400">
          {formatTime(currentTime)} / {formatTime(duration)} · scene {index + 1}/{scenes.length}
        </p>
      </div>

      <label className={cn("block text-[11px] uppercase tracking-[0.2em] text-zinc-500", compact && "hidden")}>
        Scene
        <input
          type="range"
          min={0}
          max={Math.max(0.1, duration || 0.1)}
          step={0.05}
          value={Number.isFinite(currentTime) ? currentTime : 0}
          onChange={(event) => onSeekScene(Number(event.target.value))}
          className="mt-1 h-2 w-full cursor-pointer appearance-none rounded-full bg-white/10 accent-amber-400"
          style={{ backgroundSize: `${sceneProgress}% 100%` }}
          aria-label="Seek in this scene"
        />
      </label>

      <label className={cn("block text-[11px] uppercase tracking-[0.2em] text-zinc-500", compact ? "mt-0" : "mt-3")}>
        {compact ? "Progress" : "Lesson"}
        <input
          type="range"
          min={0}
          max={lessonTotal}
          step={0.1}
          value={lessonTime}
          onChange={(event) => onSeekLesson(Number(event.target.value))}
          className="mt-1 h-2 w-full cursor-pointer appearance-none rounded-full bg-white/10 accent-amber-300"
          aria-label="Seek in the full lesson"
        />
      </label>

      <div className="mt-2 flex gap-1">
        {scenes.map((scene, sceneIndex) => (
          <button
            key={scene.id}
            type="button"
            title={`${scene.type} · scene ${sceneIndex + 1}`}
            onClick={() => onSeekLesson(lengths.slice(0, sceneIndex).reduce((sum, value) => sum + value, 0) + 0.05)}
            className={`h-1.5 flex-1 rounded-full ${sceneIndex === index ? "bg-amber-400" : "bg-white/15 hover:bg-white/30"}`}
          />
        ))}
      </div>
      <p className="mt-1 text-right text-[11px] tabular-nums text-zinc-500">
        {formatTime(lessonTime)} / {formatTime(lessonTotal)}
      </p>

      <div className={cn("flex flex-wrap items-center gap-3", compact ? "mt-2" : "mt-3")}>
        <span className="text-[11px] uppercase tracking-[0.2em] text-zinc-500">Speed</span>
        <input
          type="range"
          min={0.5}
          max={1.75}
          step={0.05}
          value={rate}
          onChange={(event) => onRate(Number(event.target.value))}
          className="h-2 w-40 cursor-pointer appearance-none rounded-full bg-white/10 accent-amber-400"
          aria-label="Playback speed"
        />
        <span className="w-12 text-xs tabular-nums text-amber-200">{rate.toFixed(2)}x</span>
        {compact ? null : (
        <div className="flex flex-wrap gap-1">
          {RATES.map((value) => (
            <button
              key={value}
              type="button"
              onClick={() => onRate(value)}
              className={`rounded-lg px-2 py-1 text-[11px] ${
                Math.abs(rate - value) < 0.001 ? "bg-amber-400 text-zinc-950" : "bg-white/5 text-zinc-300 hover:bg-white/10"
              }`}
            >
              {value}x
            </button>
          ))}
        </div>
        )}
      </div>
    </div>
  );
}
