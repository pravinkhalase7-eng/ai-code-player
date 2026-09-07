from pathlib import Path
import json
import sqlite3
import wave
import re

ROOT = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder")
LID = "les_21c34e4cfbbf47a8bc4d476d554fba51"

# --- 1) beatsFromSegments: rescale when segment clock >> real duration ---
anim = ROOT / "frontend/lib/infoReelAnim.ts"
at = anim.read_text()
old = '''/** Prefer real narration segment times; do not stretch into trailing silence. */
export function beatsFromSegments(
  segments: { start: number; end: number; text?: string }[],
  duration?: number,
): AnimBeat[] {
  const segs = (segments || [])
    .map((s, index) => ({
      text: String(s.text || "").trim(),
      index,
      start: Math.max(0, Number(s.start) || 0),
      end: Math.max(Number(s.start) || 0, Number(s.end) || 0),
    }))
    .filter((s) => s.end > s.start + 0.05);
  if (!segs.length) return [];
  const last = segs[segs.length - 1];
  const dur = Number(duration) || 0;
  // Only extend last beat if duration is near the cue end (not minutes of silence).
  if (dur > last.end + 0.2 && dur <= last.end + 2.5) {
    last.end = dur;
  }
  return segs;
}
'''
new = '''/** Prefer real narration segment times; squeeze/stretch to match actual clip duration. */
export function beatsFromSegments(
  segments: { start: number; end: number; text?: string }[],
  duration?: number,
): AnimBeat[] {
  const segs = (segments || [])
    .map((s, index) => ({
      text: String(s.text || "").trim(),
      index,
      start: Math.max(0, Number(s.start) || 0),
      end: Math.max(Number(s.start) || 0, Number(s.end) || 0),
    }))
    .filter((s) => s.end > s.start + 0.05);
  if (!segs.length) return [];
  const last = segs[segs.length - 1];
  const dur = Number(duration) || 0;
  // Planned cue clocks often overshoot short TTS (or undershoot padded files).
  if (dur > 0.4 && last.end > 0.05 && Math.abs(dur - last.end) > 0.45) {
    const scale = dur / last.end;
    return segs.map((s, index) => ({
      ...s,
      index,
      start: Math.max(0, Number((s.start * scale).toFixed(3))),
      end:
        index === segs.length - 1
          ? Number(dur.toFixed(3))
          : Math.max(0.05, Number((s.end * scale).toFixed(3))),
    }));
  }
  // Only extend last beat if duration is near the cue end (not minutes of silence).
  if (dur > last.end + 0.2 && dur <= last.end + 2.5) {
    last.end = dur;
  }
  return segs;
}
'''
if old not in at:
    raise SystemExit("beatsFromSegments block not found")
anim.write_text(at.replace(old, new, 1))
print("infoReelAnim: rescale beats to duration")

# --- 2) ReelStage: when diagram steps != segment count, drive board by equal-split steps ---
stage = ROOT / "frontend/components/player/ReelStage.tsx"
st = stage.read_text()
old_anim = '''  const infoAnim = useMemo(() => {
    if (!isConcept) return null;
    // HashMap explainers: lock phases to narration segment clocks (not equal-split of padded audio).
    const segs = scene.segments || [];
    if ((hashmapVisual || diagramSteps.length) && segs.length >= 2) {
      const beats = beatsFromSegments(segs, duration);
      return infoBulletAtBeats(beats, currentTime);
    }
    return infoBulletAt(syncTitles, currentTime, duration);
  }, [isConcept, hashmapVisual, scene.segments, syncTitles, currentTime, duration]);
'''
new_anim = '''  const infoAnim = useMemo(() => {
    if (!isConcept) return null;
    const segs = scene.segments || [];
    // When diagram step count differs from narration segments, equal-split steps across
    // the real clip duration so every phase (e.g. 5 board steps) still appears on screen.
    if (diagramSteps.length >= 2 && Math.abs(diagramSteps.length - segs.length) >= 1) {
      return infoBulletAt(stepTitles, currentTime, duration);
    }
    // Otherwise lock phases to narration segment clocks (rescaled to clip duration).
    if ((hashmapVisual || diagramSteps.length) && segs.length >= 2) {
      const beats = beatsFromSegments(segs, duration);
      return infoBulletAtBeats(beats, currentTime);
    }
    return infoBulletAt(syncTitles, currentTime, duration);
  }, [
    isConcept,
    hashmapVisual,
    diagramSteps.length,
    stepTitles,
    scene.segments,
    syncTitles,
    currentTime,
    duration,
  ]);
'''
if old_anim not in st:
    raise SystemExit("ReelStage infoAnim block not found")
stage.write_text(st.replace(old_anim, new_anim, 1))
print("ReelStage: step/seg mismatch uses equal-split")

# --- 3) LessonPlayer: prefer real audio duration always; shrink when cues overshoot ---
player = ROOT / "frontend/components/player/LessonPlayer.tsx"
pt = player.read_text()
old_lock = '''        const segEnds = (scene.segments || []).map((s) => Number(s.end) || 0);
        const lastSegEnd = segEnds.length ? Math.max(...segEnds) : 0;
        // Reel TTS sometimes pads huge trailing silence; keep board synced to cues.
        if (lastSegEnd > 1 && audio.duration > lastSegEnd + 8) {
          lockedDuration = lastSegEnd + 0.6;
        } else {
          lockedDuration = audio.duration;
        }
        setClipDuration(lockedDuration);
'''
new_lock = '''        const segEnds = (scene.segments || []).map((s) => Number(s.end) || 0);
        const lastSegEnd = segEnds.length ? Math.max(...segEnds) : 0;
        // Prefer real WAV length. Only trim huge trailing TTS silence vs cue clocks.
        if (lastSegEnd > 1 && audio.duration > lastSegEnd + 8) {
          lockedDuration = lastSegEnd + 0.6;
        } else {
          lockedDuration = audio.duration;
        }
        setClipDuration(lockedDuration);
'''
# same logic essentially - already prefers audio. Keep comment clearer; no functional change needed
# but ensure scene.duration overshoot doesn't keep playing after audio ends via wall clock
if old_lock in pt:
    player.write_text(pt.replace(old_lock, new_lock, 1))
    print("LessonPlayer: clarified lock comment")
else:
    print("LessonPlayer: lock block unchanged/missing")

# --- 4) After TTS, set duration from WAV + rescale segments ---
svc = ROOT / "backend/app/services/lesson_service.py"
sv = svc.read_text()
if "def _audio_duration_seconds" not in sv:
    helper = '''
def _audio_duration_seconds(audio_url: str | None) -> float | None:
    """Read WAV length for a stored /audio/... url."""
    if not audio_url:
        return None
    from pathlib import Path as _Path
    name = _Path(str(audio_url)).name
    for base in (
        _Path(settings.storage_dir) / "audio" if hasattr(settings, "storage_dir") else None,
        _Path(__file__).resolve().parents[2] / "storage" / "audio",
        _Path(__file__).resolve().parents[3] / "storage" / "audio",
    ):
        if base is None:
            continue
        path = base / name
        if not path.is_file():
            continue
        try:
            with wave.open(str(path), "rb") as handle:
                rate = float(handle.getframerate() or 1)
                frames = float(handle.getnframes() or 0)
                if rate > 0 and frames > 0:
                    return frames / rate
        except Exception:
            return None
    return None


def _align_scene_to_audio(scene: Any, audio_url: str | None) -> Any:
    """Snap scene.duration + segments to the real TTS WAV so board/cues match speech."""
    dur = _audio_duration_seconds(audio_url)
    if not dur or dur < 0.4:
        return scene
    dur = round(float(dur), 2)
    segments = list(getattr(scene, "segments", None) or [])
    if not segments:
        return scene.model_copy(update={"duration": dur, "audio_url": audio_url or scene.audio_url})
    last = max(float(getattr(s, "end", 0) or 0) for s in segments) or 0.0
    if last <= 0.05:
        return scene.model_copy(update={"duration": dur, "audio_url": audio_url or scene.audio_url})
    scale = dur / last
    updated = []
    for seg in segments:
        start = round(float(seg.start or 0) * scale, 2)
        end = round(float(seg.end or 0) * scale, 2)
        updated.append(seg.model_copy(update={"start": start, "end": max(start + 0.05, end)}))
    if updated:
        updated[-1] = updated[-1].model_copy(update={"end": dur})
    return scene.model_copy(
        update={"duration": dur, "segments": updated, "audio_url": audio_url or scene.audio_url}
    )

'''
    if "import wave" not in sv:
        sv = sv.replace("import re\n", "import re\nimport wave\n", 1)
    # insert before generate_lesson_assets or after _spoken_scene_text
    marker = "def lesson_needs_google_audio(lesson: Lesson) -> bool:"
    if marker not in sv:
        raise SystemExit("lesson_needs_google_audio not found")
    sv = sv.replace(marker, helper + marker, 1)

    # In generate_lesson_assets, after scene_patch audio_url, align
    old_upd = '''        scene_patch["audio_url"] = audio_url
        updated = scene.model_copy(update=scene_patch)
        updated_scenes.append(updated)
'''
    new_upd = '''        scene_patch["audio_url"] = audio_url
        updated = scene.model_copy(update=scene_patch)
        updated = _align_scene_to_audio(updated, audio_url)
        updated_scenes.append(updated)
'''
    if old_upd not in sv:
        raise SystemExit("generate_lesson_assets update block not found")
    sv = sv.replace(old_upd, new_upd, 1)
    svc.write_text(sv)
    print("lesson_service: align duration to WAV after TTS")
else:
    print("lesson_service: align already present")

# --- 5) Repair this lesson in DB ---
def wav_dur(path: Path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / float(w.getframerate())

def rescale_segs(segs, duration):
    if not segs:
        return segs
    last = max(float(s.get("end") or 0) for s in segs) or 0
    if last <= 0.05:
        return segs
    scale = duration / last
    out = []
    for i, s in enumerate(segs):
        start = round(float(s.get("start") or 0) * scale, 2)
        end = round(float(s.get("end") or 0) * scale, 2)
        ns = dict(s)
        ns["start"] = start
        ns["end"] = duration if i == len(segs) - 1 else max(start + 0.05, end)
        out.append(ns)
    return out

con = sqlite3.connect(ROOT / "backend" / "tutor.db")
row = con.execute("select lesson_json from lessons where id=?", (LID,)).fetchone()
if not row:
    print("lesson missing")
else:
    p = json.loads(row[0])
    audio_root = ROOT / "storage" / "audio"
    for s in p.get("scenes") or []:
        url = s.get("audio_url") or ""
        name = Path(url).name
        path = audio_root / name
        if not path.is_file():
            print("missing audio", name)
            continue
        d = round(wav_dur(path), 2)
        old_d = s.get("duration")
        s["duration"] = d
        s["segments"] = rescale_segs(s.get("segments") or [], d)
        print(f"scene {s.get('type')}: {old_d} -> {d}, segs last={s['segments'][-1]['end'] if s['segments'] else None}")
    con.execute(
        "update lessons set lesson_json=? where id=?",
        (json.dumps(p, ensure_ascii=False), LID),
    )
    con.commit()
    print("lesson repaired", LID)
con.close()
print("done")
