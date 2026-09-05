"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Download, ImageIcon, Pencil, Sparkles, TerminalSquare, Volume2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { CodeWorkbench } from "@/components/editor/CodeWorkbench";
import { QuizCard } from "@/components/player/QuizCard";
import { ExecutionStepper } from "@/components/player/ExecutionStepper";
import { PlayerTransport } from "@/components/player/PlayerTransport";
import { Terminal } from "@/components/player/Terminal";
import { TutorAvatar } from "@/components/tutor/TutorAvatar";
import { ReelStage } from "@/components/player/ReelStage";
import { ReelScriptStudio, type ScriptLine } from "@/components/player/ReelScriptStudio";
import { answerQuiz, executeCode, explainRunError, generateThumbnail, saveProgress, saveReelScript, sendChat } from "@/lib/api";
import { downloadBlob, exportReelVideo, fileExtension } from "@/lib/reelExport";
import { runCommand, sourceFilename } from "@/lib/language";
import { audioSrc, cn } from "@/lib/utils";
import { firstMeaningfulHighlight } from "@/lib/codeFocus";
import { stripDurationNoise } from "@/lib/reelHeadlines";
import { buildCues, cueAt } from "@/lib/narrationSync";
import { SPOKEN_LANGUAGES } from "@/lib/spokenLanguage";
import type { ExecutionStep, HighlightRange, Lesson, LessonScene, RunHelp, TutorExpression } from "@/types/lesson";

export function LessonPlayer({
  lesson,
  warnings,
  initialSceneIndex = 0,
  onLessonChange,
}: {
  lesson: Lesson;
  warnings: string[];
  initialSceneIndex?: number;
  onLessonChange?: (lesson: Lesson) => void;
}) {
  const scenes = lesson.scenes;
  const [index, setIndex] = useState(() =>
    Math.min(Math.max(0, initialSceneIndex), Math.max(0, lesson.scenes.length - 1)),
  );
  const [playing, setPlaying] = useState(false);
  const [rate, setRate] = useState(1);
  const explainOnly = useMemo(() => isExplainLesson(lesson), [lesson]);
  const exampleCode = useMemo(() => primaryCode(lesson), [lesson]);
  const [code, setCode] = useState(exampleCode);
  const [highlight, setHighlight] = useState<HighlightRange | null>(null);
  const [expression, setExpression] = useState<TutorExpression>("explaining");
  const [caption, setCaption] = useState(scenes[index]?.narration ?? "");
  const [stepIndex, setStepIndex] = useState(0);
  const [manualStepping, setManualStepping] = useState(false);
  const [liveSteps, setLiveSteps] = useState<ExecutionStep[] | null>(null);
  const [runHelp, setRunHelp] = useState<RunHelp | null>(null);
  const [runBusy, setRunBusy] = useState(false);
  const resumedFrom = initialSceneIndex > 0 ? initialSceneIndex : 0;
  const [runOutput, setRunOutput] = useState<string[]>([]);
  const [runError, setRunError] = useState("");
  const [chat, setChat] = useState("");
  const [messages, setMessages] = useState<{ role: string; text: string }[]>([]);
  const [quizResult, setQuizResult] = useState<{ status: string; explanation: string } | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [clipDuration, setClipDuration] = useState(0);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const started = useRef(Date.now());
  const scene = scenes[index];
  const [needsGesture, setNeedsGesture] = useState(true);
  const [thumbUrl, setThumbUrl] = useState(lesson.thumbnail_url || "");
  const [thumbBusy, setThumbBusy] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [exportLabel, setExportLabel] = useState("");
  const [videoBlob, setVideoBlob] = useState<Blob | null>(null);
  const [reelReview, setReelReview] = useState(() => lesson.format === "reel");
  const [draftCode, setDraftCode] = useState(() => exampleCode);
  const [draftLines, setDraftLines] = useState<ScriptLine[]>(() => scriptLinesFrom(lesson));
  const [scriptBusy, setScriptBusy] = useState("");
  const [scriptError, setScriptError] = useState("");
  const pendingPlay = useRef(false);
  const indexRef = useRef(index);
  const playingRef = useRef(playing);
  indexRef.current = index;
  playingRef.current = playing;

  useEffect(() => {
    setCaption(scene?.narration ?? "");
    setExpression(scene?.expression ?? "explaining");
    setStepIndex(0);
    setManualStepping(false);
    setLiveSteps(null);
    setRunHelp(null);
    setCode(explainOnly ? "" : scene?.code?.trim() ? scene.code : exampleCode || "");
    setCurrentTime(0);
    if (scene?.type === "code") {
      setHighlight(firstMeaningfulHighlight(scene.code || exampleCode, scene.highlight_ranges ?? []) ?? null);
    } else if (scene?.type === "execution") {
      setHighlight(
        scene.iterations?.[0]
          ? { start_line: scene.iterations[0].line, end_line: scene.iterations[0].line, start_col: 0, label: "step" }
          : null,
      );
    } else {
      setHighlight(null);
    }
  }, [index, scene, exampleCode, explainOnly]);

  useEffect(() => {
    if (lesson.format !== "reel") return;
    const incoming = lesson.thumbnail_url || "";
    if (incoming.includes("?v=")) {
      setThumbUrl(incoming);
      return;
    }
    let cancelled = false;
    void generateThumbnail(lesson.lesson_id)
      .then((payload) => {
        if (!cancelled) setThumbUrl(payload.lesson.thumbnail_url || "");
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [lesson.format, lesson.lesson_id, lesson.thumbnail_url]);

  const lastPlayed = useRef("");
  const waitingForVoice = playing && !audioSrc(scene?.audio_url);

  function advanceScene() {
    if (!playingRef.current) return;
    const next = indexRef.current + 1;
    if (next < scenes.length) {
      setIndex(next);
      setPlaying(true);
      void playClip(scenes[next], false);
      return;
    }
    setPlaying(false);
  }

  async function playClip(target: LessonScene | undefined, fromUser: boolean, startAt?: number) {
    window.speechSynthesis?.cancel();
    const el = audioRef.current;
    const url = audioSrc(target?.audio_url);
    const key = `${target?.id}:${url}`;
    if (!el || !url) {
      if (fromUser) setNeedsGesture(false);
      return;
    }
    el.pause();
    el.src = url;
    el.load();
    el.volume = 1;
    el.muted = false;
    el.playbackRate = rate;
    const applyStart = () => {
      if (startAt === undefined) return;
      if (Number.isFinite(el.duration) && el.duration > 0) {
        el.currentTime = Math.min(startAt, el.duration);
        setCurrentTime(el.currentTime);
      }
    };
    el.addEventListener("loadedmetadata", applyStart, { once: true });
    try {
      await el.play();
      applyStart();
      lastPlayed.current = key;
      setNeedsGesture(false);
    } catch (error) {
      const name = error instanceof DOMException ? error.name : "";
      if (name === "NotAllowedError") {
        setNeedsGesture(true);
        setPlaying(false);
        return;
      }
      try {
        await new Promise((resolve) => window.setTimeout(resolve, 250));
        await el.play();
        lastPlayed.current = key;
        setNeedsGesture(false);
      } catch {
        setNeedsGesture(true);
      }
    }
  }

  useEffect(() => {
    const el = audioRef.current;
    if (!el) return undefined;
    const onEnded = () => advanceScene();
    el.addEventListener("ended", onEnded);
    return () => el.removeEventListener("ended", onEnded);
  }, [scenes]);

  function startVoice() {
    setNeedsGesture(false);
    setPlaying(true);
    void playClip(scene, true);
  }

  useEffect(() => {
    if (reelReview || !pendingPlay.current) return;
    pendingPlay.current = false;
    setNeedsGesture(false);
    setPlaying(true);
    void playClip(scene, true);
  }, [reelReview, scene]);

  function goTo(nextIndex: number, startAt = 0) {
    const bounded = Math.min(scenes.length - 1, Math.max(0, nextIndex));
    setIndex(bounded);
    setPlaying(true);
    void playClip(scenes[bounded], true, startAt);
  }

  function seekScene(time: number) {
    const audio = audioRef.current;
    if (audio && Number.isFinite(audio.duration) && audio.duration > 0) {
      audio.currentTime = Math.min(Math.max(0, time), audio.duration);
      setCurrentTime(audio.currentTime);
      return;
    }
    setCurrentTime(Math.max(0, time));
  }

  function seekLesson(time: number) {
    const lengths = scenes.map((item, sceneIndex) =>
      sceneIndex === index && clipDuration > 0.4 ? clipDuration : Math.max(3, item.duration || 8),
    );
    let cursor = 0;
    for (let sceneIndex = 0; sceneIndex < scenes.length; sceneIndex += 1) {
      const length = lengths[sceneIndex];
      if (cursor + length >= time) {
        const offset = Math.max(0, time - cursor);
        if (sceneIndex === index) {
          seekScene(offset);
          return;
        }
        goTo(sceneIndex, offset);
        return;
      }
      cursor += length;
    }
    goTo(scenes.length - 1);
  }

  function setPlaybackRate(value: number) {
    const next = Math.min(1.75, Math.max(0.5, value));
    setRate(next);
    if (audioRef.current) audioRef.current.playbackRate = next;
  }

  useEffect(() => {
    if (audioRef.current) audioRef.current.playbackRate = rate;
  }, [rate]);

  useEffect(() => {
    if (playing) return undefined;
    audioRef.current?.pause();
    window.speechSynthesis?.cancel();
    return undefined;
  }, [playing]);

  useEffect(() => {
    if (!playing || !scene) return;
    const url = audioSrc(scene.audio_url);
    if (!url) {
      lastPlayed.current = `${scene.id}:`;
      return;
    }
    if (lastPlayed.current === `${scene.id}:`) {
      void playClip(scene, false);
    }
  }, [scene?.audio_url, scene?.id, playing]);

  useEffect(() => {
    if (!playing || !scene) return undefined;
    const speechStarted = Date.now();
    let lockedDuration: number | undefined;
    let frame = 0;
    const tick = () => {
      const audio = audioRef.current;
      if (audio && Number.isFinite(audio.duration) && audio.duration > 0.4) {
        lockedDuration = audio.duration;
        setClipDuration(audio.duration);
      }
      const cues = buildCues(scene, lockedDuration);
      let time = 0;
      if (audio && !audio.paused && Number.isFinite(audio.currentTime) && audio.currentTime > 0.05) {
        time = audio.currentTime;
      } else {
        time = ((Date.now() - speechStarted) / 1000) * rate;
      }
      setCurrentTime(time);
      const cue = cueAt(cues, time);
      if (cue) {
        setCaption(cue.text);
        if (cue.highlight) {
          setHighlight(cue.highlight);
        } else if (scene.type !== "code") {
          setHighlight(null);
        }
        if (cue.expression) setExpression(cue.expression);
        if (!manualStepping && typeof cue.stepIndex === "number") setStepIndex(cue.stepIndex);
      }
      frame = window.requestAnimationFrame(tick);
    };
    frame = window.requestAnimationFrame(tick);
    return () => window.cancelAnimationFrame(frame);
  }, [playing, scene, rate, index, manualStepping]);

  useEffect(() => {
    const percent = scenes.length ? ((index + 1) / scenes.length) * 100 : 0;
    void saveProgress(lesson.lesson_id, {
      current_scene: scene?.id,
      scene_index: index,
      completion_percent: percent,
      time_spent_ms: Date.now() - started.current,
    });
  }, [index, lesson.lesson_id, scene?.id, scenes.length]);

  const iterations = liveSteps ?? scene?.iterations ?? [];
  const terminalLines = useMemo(() => {
    if (runOutput.length) return runOutput;
    if (scene?.type === "terminal") return scene.stdout ?? [];
    if (iterations.length) {
      return iterations
        .slice(0, stepIndex + 1)
        .map((step) => step.output_line)
        .filter((line): line is string => Boolean(line));
    }
    return [];
  }, [runOutput, scene, stepIndex, iterations]);

  async function runStudentCode() {
    setPlaying(false);
    audioRef.current?.pause();
    setRunBusy(true);
    setRunHelp(null);
    setExpression("thinking");
    try {
      const result = await executeCode(lesson.language, code, lesson.lesson_id);
      setRunOutput(result.stdout);
      setRunError(
        result.timed_out
          ? "Execution stopped because the program exceeded the time limit."
          : result.compile_error
            ? `Compilation Error\n${result.stderr}`
            : result.stderr,
      );
      if (result.iterations?.length) {
        setLiveSteps(result.iterations);
        setStepIndex(0);
        setManualStepping(true);
      }
      if (result.success) {
        setExpression("celebrating");
        setCaption("That ran. Step through the output on the left if you want to see each beat.");
        return;
      }
      setExpression("confused");
      const help = await explainRunError({
        language: lesson.language,
        code,
        stderr: result.stderr,
        compile_error: result.compile_error,
        timed_out: result.timed_out,
        lesson_id: lesson.lesson_id,
      });
      setRunHelp(help);
      setCaption(help.explanation);
      if (help.line) {
        setHighlight({
          start_line: help.line,
          end_line: help.line,
          start_col: 0,
          label: help.label || "error",
        });
      }
    } catch (err) {
      setRunError(err instanceof Error ? err.message : "Could not run the code.");
      setExpression("confused");
    } finally {
      setRunBusy(false);
    }
  }

  function takeStep(next: number) {
    if (!iterations.length) return;
    const bounded = Math.min(iterations.length - 1, Math.max(0, next));
    setManualStepping(true);
    setPlaying(false);
    audioRef.current?.pause();
    setStepIndex(bounded);
    const step = iterations[bounded];
    if (step) {
      setCaption(step.description);
      setHighlight({
        start_line: step.line,
        end_line: step.line,
        start_col: 0,
        label: step.label,
      });
    }
  }

  async function ask() {
    if (!chat.trim()) return;
    const message = chat.trim();
    setChat("");
    setMessages((current) => [...current, { role: "student", text: message }]);
    setExpression("listening");
    const reply = await sendChat(lesson.lesson_id, message);
    setMessages((current) => [...current, { role: "tutor", text: reply.reply }]);
    setExpression((reply.expression as TutorExpression) || "explaining");
    if (reply.execution) {
      setRunOutput(reply.execution.stdout);
      setRunError(
        reply.execution.timed_out
          ? "Execution stopped because the program exceeded the time limit."
          : reply.execution.stderr,
      );
    }
  }

  async function makeThumbnail() {
    setThumbBusy(true);
    try {
      const payload = await generateThumbnail(lesson.lesson_id);
      setThumbUrl(payload.lesson.thumbnail_url || "");
    } catch (err) {
      setExportLabel(err instanceof Error ? err.message : "Could not generate a thumbnail");
    } finally {
      setThumbBusy(false);
    }
  }

  function openScriptStudio() {
    setPlaying(false);
    audioRef.current?.pause();
    window.speechSynthesis?.cancel();
    setScriptError("");
    setDraftCode(code || exampleCode);
    setDraftLines(scriptLinesFrom(lesson));
    setReelReview(true);
  }

  function scriptIsDirty() {
    if ((draftCode || "").trim() !== (exampleCode || "").trim()) return true;
    return lesson.scenes.some((item) => {
      const line = draftLines.find((entry) => entry.id === item.id);
      return (line?.narration ?? "") !== (item.narration ?? "");
    });
  }

  async function persistDraft() {
    const payload = await saveReelScript(lesson.lesson_id, {
      code: draftCode,
      scenes: draftLines,
      rewrite: false,
    });
    onLessonChange?.(payload.lesson);
    setThumbUrl(payload.lesson.thumbnail_url || "");
    setDraftCode(primaryCode(payload.lesson) || draftCode);
    setDraftLines(scriptLinesFrom(payload.lesson));
    return payload.lesson;
  }

  async function playReviewedShort() {
    setScriptError("");
    try {
      if (scriptIsDirty()) {
        setScriptBusy("save");
        await persistDraft();
      }
      pendingPlay.current = true;
      setIndex(0);
      setReelReview(false);
    } catch (err) {
      setScriptError(err instanceof Error ? err.message : "Could not save the script");
    } finally {
      setScriptBusy("");
    }
  }

  async function rewriteFromProgram() {
    setScriptBusy("rewrite");
    setScriptError("");
    try {
      const payload = await saveReelScript(lesson.lesson_id, {
        code: draftCode,
        scenes: draftLines,
        rewrite: true,
      });
      onLessonChange?.(payload.lesson);
      setThumbUrl(payload.lesson.thumbnail_url || "");
      setDraftCode(primaryCode(payload.lesson) || draftCode);
      setDraftLines(scriptLinesFrom(payload.lesson));
    } catch (err) {
      setScriptError(err instanceof Error ? err.message : "Could not rewrite the script from that program");
    } finally {
      setScriptBusy("");
    }
  }

  async function confirmScriptAndRecord() {
    setScriptBusy("save");
    setScriptError("");
    try {
      const next = scriptIsDirty() ? await persistDraft() : lesson;
      setReelReview(false);
      await recordReelVideo(next);
    } catch (err) {
      setScriptError(err instanceof Error ? err.message : "Could not save the script");
      setScriptBusy("");
    }
  }

  async function downloadReel() {
    if (videoBlob && !exporting) {
      downloadBlob(videoBlob, `${safeReelName(lesson.topic)}.${fileExtension(videoBlob)}`);
      setExportLabel("Downloaded — tap Download again anytime");
      return;
    }
    if (reelReview) {
      try {
        const next = scriptIsDirty() ? await persistDraft() : lesson;
        setReelReview(false);
        await recordReelVideo(next);
      } catch (err) {
        setExportLabel(err instanceof Error ? err.message : "Could not export the reel");
      }
      return;
    }
    await recordReelVideo(lesson);
  }

  async function recordReelVideo(source: Lesson) {
    setScriptBusy("record");
    setExporting(true);
    setExportLabel("Recording 9:16 reel…");
    setPlaying(false);
    audioRef.current?.pause();
    window.speechSynthesis?.cancel();
    try {
      let poster = thumbUrl || source.thumbnail_url || "";
      if (!poster) {
        setExportLabel("Making thumbnail…");
        try {
          const payload = await generateThumbnail(source.lesson_id);
          poster = payload.lesson.thumbnail_url || "";
          setThumbUrl(poster);
        } catch {
          poster = "";
        }
      }
      const blob = await exportReelVideo(
        { ...source, thumbnail_url: poster || source.thumbnail_url },
        (progress) => setExportLabel(`Scene ${progress.scene}/${progress.total} · ${progress.label}`),
      );
      setVideoBlob(blob);
      setExportLabel("Reel ready — download it");
      downloadBlob(blob, `${safeReelName(source.topic)}.${fileExtension(blob)}`);
    } catch (err) {
      setExportLabel(err instanceof Error ? err.message : "Could not generate the reel video");
    } finally {
      setExporting(false);
      setScriptBusy("");
    }
  }

  if (!scene) return null;

  const isReel = lesson.format === "reel";
  const spokenLabel =
    SPOKEN_LANGUAGES.find((item) => item.id === (lesson.spoken_language || "en"))?.label || "English";

  return (
    <div
      className={cn(
        isReel && reelReview
          ? "flex min-h-[calc(100dvh-3.25rem)] flex-col gap-3"
          : isReel
            ? "flex h-[calc(100dvh-3.25rem)] flex-col gap-2 overflow-hidden"
            : "grid min-h-[calc(100vh-6rem)] grid-rows-[auto_1fr_auto_auto] gap-4",
      )}
    >
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm uppercase tracking-[0.25em] text-amber-200/80">
            {isReel
              ? lesson.requires_code === false ? `${spokenLabel} · Explain · ${lesson.topic}` : `${spokenLabel} · ${lesson.language} · ${lesson.topic}`
              : `Scene ${index + 1} of ${scenes.length} · ${scene.type}`}
          </p>
          <h1 className={cn("font-semibold text-white", isReel ? "text-2xl leading-7" : "text-2xl")}>{isReel ? lesson.topic : lesson.title}</h1>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {isReel ? (
            <>
              {!reelReview ? (
                <Button size="sm" variant="outline" onClick={openScriptStudio} disabled={exporting || Boolean(scriptBusy)}>
                  <Pencil className="h-4 w-4" /> Edit script
                </Button>
              ) : null}
              <Button size="sm" variant="outline" onClick={() => void makeThumbnail()} disabled={thumbBusy || exporting}>
                <ImageIcon className="h-4 w-4" /> {thumbBusy ? "Thumbnail…" : "Thumbnail"}
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => void downloadReel()}
                disabled={exporting || Boolean(scriptBusy)}
              >
                <Download className="h-4 w-4" />
                {exporting
                  ? "Exporting…"
                  : videoBlob
                    ? "Download"
                    : "Download video"}
              </Button>
            </>
          ) : (
            <Button size="sm" onClick={() => void runStudentCode()} disabled={runBusy}>
              <TerminalSquare className="h-4 w-4" /> {runBusy ? "Running…" : "Run code"}
            </Button>
          )}
        </div>
      </header>
      {isReel && exportLabel ? (
        <p className="-mt-2 text-xs text-zinc-400">{exportLabel}</p>
      ) : null}

      {isReel && reelReview ? (
        <ReelScriptStudio
          lesson={lesson}
          code={explainOnly ? "" : draftCode}
          lines={draftLines}
          busy={scriptBusy}
          error={scriptError}
          onCodeChange={setDraftCode}
          onNarrationChange={(id, narration) =>
            setDraftLines((current) => current.map((line) => (line.id === id ? { ...line, narration } : line)))
          }
          onRewrite={() => void rewriteFromProgram()}
          onPlay={() => void playReviewedShort()}
          onRecord={() => void confirmScriptAndRecord()}
          onDownload={() => void downloadReel()}
          downloading={exporting}
          explainOnly={explainOnly}
        />
      ) : (
        <>
      <PlayerTransport
        scenes={scenes}
        index={index}
        currentTime={currentTime}
        duration={clipDuration || scene.duration || 8}
        playing={playing}
        rate={rate}
        compact={isReel}
        onPlayPause={() => {
          if (playing) {
            setPlaying(false);
            audioRef.current?.pause();
            window.speechSynthesis?.cancel();
            return;
          }
          startVoice();
        }}
        onRate={setPlaybackRate}
        onSeekScene={seekScene}
        onSeekLesson={seekLesson}
        onPrev={() => goTo(index - 1)}
        onNext={() => goTo(index + 1)}
        onReplay={() => goTo(index, 0)}
      />

      {resumedFrom > 0 && index === resumedFrom ? (
        <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm text-zinc-300">
          <span>Resumed at scene {index + 1}. Byte will pick up from here.</span>
          <button type="button" className="text-amber-200 hover:underline" onClick={() => goTo(0)}>
            Start from the beginning
          </button>
        </div>
      ) : null}

      {needsGesture ? (
        <button
          type="button"
          onClick={startVoice}
          className={cn(
            "flex items-center justify-center gap-2 rounded-xl border border-amber-300/40 bg-amber-400 text-sm font-semibold text-zinc-950",
            isReel ? "px-3 py-2" : "px-4 py-3",
          )}
        >
          <Volume2 className="h-4 w-4" />
          {isReel ? "Tap to play Byte’s voice" : "Click to hear Byte — uses Google Cloud Chirp, not the browser voice"}
        </button>
      ) : null}

      {waitingForVoice ? (
        <p className="rounded-xl border border-amber-300/20 bg-amber-400/10 px-4 py-2 text-sm text-amber-100">
          Preparing Byte’s natural voice… playback starts as soon as the audio file is ready.
        </p>
      ) : null}

      {warnings.length ? (
        <p className="rounded-xl border border-amber-300/20 bg-amber-400/10 px-4 py-2 text-sm text-amber-100">
          {warnings[0]}
        </p>
      ) : null}

      {isReel ? (
        <div className="mx-auto flex min-h-0 w-full flex-1 items-center justify-center overflow-hidden">
          <ReelStage
            lesson={{ ...lesson, thumbnail_url: thumbUrl || lesson.thumbnail_url }}
            scene={scene}
            code={explainOnly ? "" : code}
            caption={stripDurationNoise(caption)}
            highlight={highlight}
            playing={playing}
            currentTime={currentTime}
            duration={clipDuration || scene.duration || 8}
            terminalLines={terminalLines}
            runError={runError}
            iterations={iterations}
            sceneIndex={index}
            sceneCount={scenes.length}
            stepIndex={stepIndex}
          />
        </div>
      ) : (
        <>
          <div className="grid gap-4 lg:grid-cols-[minmax(260px,0.9fr)_minmax(0,1.4fr)]">
            <section className="rounded-3xl border border-white/10 bg-white/5 p-5">
              <TutorAvatar expression={expression} speaking={playing} gesture="point_right" />
              <p className="mt-4 text-sm leading-6 text-zinc-200">{stripDurationNoise(caption)}</p>
              {highlight?.label ? (
                <p className="mt-2 text-xs uppercase tracking-[0.2em] text-amber-300/80">
                  Highlighting {highlight.label}
                </p>
              ) : null}
              {runHelp ? (
                <div className="mt-4 space-y-3 rounded-2xl border border-red-400/30 bg-red-400/10 p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.2em] text-red-200">
                    {runHelp.issue}
                    {runHelp.line ? ` · line ${runHelp.line}` : ""}
                  </p>
                  <p className="text-sm leading-6 text-red-50">{runHelp.explanation}</p>
                  {runHelp.suggested_code ? (
                    <Button
                      size="sm"
                      onClick={() => {
                        setCode(runHelp.suggested_code || "");
                        setRunHelp(null);
                        setCaption("I applied the fix in the editor. Click Run to see if it compiles.");
                        setExpression("explaining");
                      }}
                    >
                      Apply Byte’s fix
                    </Button>
                  ) : null}
                </div>
              ) : null}
              {scene.type === "concept" && scene.bullets?.length ? (
                <ul className="mt-4 space-y-2 text-sm text-amber-100">
                  {scene.bullets.map((item) => (
                    <li key={item}>• {item}</li>
                  ))}
                </ul>
              ) : null}
              {iterations.length ? (
                <ExecutionStepper
                  steps={iterations}
                  stepIndex={stepIndex}
                  manual={manualStepping}
                  onStep={takeStep}
                  onRestart={() => takeStep(0)}
                />
              ) : null}
              {scene.type === "quiz" ? (
                <div className="mt-4">
                  <QuizCard
                    scene={scene}
                    result={quizResult}
                    onSubmit={async (answer, submittedCode) => {
                      const response = await answerQuiz(scene.id, answer, submittedCode);
                      setQuizResult(response.evaluation);
                      setExpression(response.evaluation.status === "correct" ? "celebrating" : "confused");
                    }}
                  />
                </div>
              ) : null}
            </section>
            <CodeWorkbench
              code={code}
              language={lesson.language}
              filename={scene.filename || sourceFilename(lesson.language)}
              highlight={highlight}
              onChange={setCode}
            />
          </div>

          <Terminal
            command={scene.command || runCommand(lesson.language)}
            lines={terminalLines}
            stderr={runError || scene.stderr}
            success={!runError}
          />

          <form
            className="flex gap-3"
            onSubmit={(event) => {
              event.preventDefault();
              void ask();
            }}
          >
            <input
              value={chat}
              onChange={(event) => setChat(event.target.value)}
              placeholder="Ask your tutor..."
              className="h-12 flex-1 rounded-2xl border border-white/10 bg-zinc-950/70 px-4 text-sm outline-none focus:border-amber-300/40"
            />
            <Button type="submit">
              <Sparkles className="h-4 w-4" /> Ask
            </Button>
          </form>
          {messages.length ? (
            <div className="space-y-2 text-sm">
              {messages.slice(-4).map((item, messageIndex) => (
                <p key={`${item.role}-${messageIndex}`} className={item.role === "tutor" ? "text-amber-100" : "text-zinc-300"}>
                  <span className="font-semibold">{item.role === "tutor" ? "Byte" : "You"}: </span>
                  {item.text}
                </p>
              ))}
            </div>
          ) : null}
        </>
      )}
        </>
      )}
      <audio ref={audioRef} className="sr-only" preload="auto" playsInline />
    </div>
  );
}

function scriptLinesFrom(lesson: Lesson): ScriptLine[] {
  return lesson.scenes.map((item) => ({
    id: item.id,
    type: item.type,
    narration: item.narration,
    takeaways: item.takeaways,
  }));
}

function isExplainLesson(lesson: Lesson): boolean {
  if (lesson.requires_code === false) return true;
  const types = new Set(lesson.scenes.map((item) => item.type));
  if (types.has("concept") && !types.has("code") && !types.has("execution")) return true;
  const topic = (lesson.topic || "").toLowerCase();
  const conceptual =
    /\b(rag|agentic|llm|llms|chatgpt|transformer|neural|prompt engineering|embedding|hallucinat|retrieval|vector db|multi-agent)\b/.test(topic) ||
    /^(what is|what.s|whats|explain|define)\b/.test(topic);
  if (lesson.format === "reel" && conceptual) return true;
  if (types.has("concept")) {
    const code = lesson.scenes.map((s) => s.code || "").join("\n");
    if (/for\s+i\s+in\s+range\s*\(\s*[0-9]+\s*\)/.test(code) || /for\s*\(\s*let\s+i\s*=\s*0/.test(code)) {
      return true;
    }
  }
  return false;
}

function primaryCode(lesson: Lesson): string {
  if (isExplainLesson(lesson)) return "";
  const scenes = [...lesson.scenes].filter((item) => (item.code || "").trim().length > 20);
  const preferred = scenes.find((item) => item.type === "code") || scenes[0];
  return preferred?.code || "";
}

function safeReelName(topic: string): string {
  const slug = topic.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  return `reel-${slug || "short"}`;
}
