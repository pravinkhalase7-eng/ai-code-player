from pathlib import Path

path = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder/frontend/components/player/LearnClient.tsx")
text = path.read_text()

old_poll = '''    async function poll() {
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
'''

new_poll = '''    async function poll() {
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
          // Soft timeout: stop spinning forever if the worker died mid-run.
          if (Date.now() - begun > 180000) {
            setError("This lesson is taking too long. Start a new one, or retry.");
            return;
          }
          window.setTimeout(poll, 1500);
          return;
        }
        // Unblock the player immediately; don't wait on progress.
        if (!progressLoaded.current) {
          progressLoaded.current = true;
          setProgressIndex(0);
          void getProgress(lessonId)
            .then((progress) => {
              if (cancelled) return;
              const startAt =
                progress.completion_percent >= 99
                  ? 0
                  : Math.max(0, progress.scene_index || 0);
              setProgressIndex(startAt);
            })
            .catch(() => undefined);
        }
        const missingAudio = payload.lesson.scenes.some((item) => !item.audio_url);
        // Only keep polling briefly for late TTS/audio — not a full 2 minutes once ready.
        if (missingAudio && Date.now() - begun < 90000) {
          window.setTimeout(poll, 2000);
        }
      } catch (err) {
        if (cancelled) return;
        const message = err instanceof Error ? err.message : String(err);
        // Deleted / missing lesson — fail fast instead of "generating" forever.
        if (/404|not found|does not exist/i.test(message)) {
          setError("This lesson is gone (maybe cleared). Start a new one from home.");
          setStatus("failed");
          return;
        }
        if (Date.now() - begun < 60000) {
          window.setTimeout(poll, 2000);
          return;
        }
        setError("Could not reach the tutor API. Check that it is running, then try again.");
      }
    }
'''

if old_poll not in text:
    raise SystemExit("poll block not found")
text = text.replace(old_poll, new_poll, 1)

# show retry sooner
text = text.replace("{elapsed >= 90 ? (", "{elapsed >= 45 ? (")

path.write_text(text)
print("LearnClient patched")

# Also harden resume: reset stale running jobs (>10 min) back to queued before force_local
jobs = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder/backend/app/services/jobs.py")
jt = jobs.read_text()
old_res = '''    elif match.status in {"completed", "failed"}:
        match.status = "queued"
        match.error = None
        match.progress = 0
        db.commit()

    # Stuck queued lessons: prefer an in-process thread so a dead Celery worker cannot block the UI.
    enqueue(match.id, "lesson_generation", force_local=True)
'''
new_res = '''    elif match.status in {"completed", "failed"}:
        match.status = "queued"
        match.error = None
        match.progress = 0
        db.commit()
    elif match.status == "running":
        # Uvicorn --reload / crashed threads leave jobs marked running forever.
        from datetime import datetime, timezone

        updated = match.updated_at
        try:
            age_s = (datetime.now(timezone.utc).replace(tzinfo=None) - (updated.replace(tzinfo=None) if getattr(updated, "tzinfo", None) else updated)).total_seconds()
        except Exception:
            age_s = 9999
        if age_s > 120:
            match.status = "queued"
            match.progress = 0
            match.error = None
            db.commit()

    # Stuck queued lessons: prefer an in-process thread so a dead Celery worker cannot block the UI.
    enqueue(match.id, "lesson_generation", force_local=True)
'''
if old_res not in jt:
    print("WARNING resume block not patched")
else:
    jobs.write_text(jt.replace(old_res, new_res, 1))
    print("resume stale running patched")
