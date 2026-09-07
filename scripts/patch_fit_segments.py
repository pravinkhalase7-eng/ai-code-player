from pathlib import Path
import ast

path = Path("backend/app/agents/orchestrator.py")
text = path.read_text()

helper = '''
def _rescale_scene_segments(scene, duration: float):
    """Stretch/squeeze narration segments so the last end matches scene duration."""
    segments = list(getattr(scene, "segments", None) or [])
    if not segments or duration <= 0.2:
        return scene
    last = max(float(getattr(s, "end", 0) or 0) for s in segments) or 0.0
    if last <= 0.05:
        return scene
    scale = duration / last
    updated = []
    for seg in segments:
        start = round(float(seg.start or 0) * scale, 2)
        end = round(float(seg.end or 0) * scale, 2)
        updated.append(seg.model_copy(update={"start": start, "end": max(start + 0.05, end)}))
    if updated:
        updated[-1] = updated[-1].model_copy(update={"end": round(duration, 2)})
    return scene.model_copy(update={"segments": updated})

'''

if "_rescale_scene_segments" not in text:
    # insert before _fit_scene_durations
    anchor = "def _fit_scene_durations(lesson: Lesson) -> Lesson:"
    if anchor not in text:
        raise SystemExit("anchor missing")
    text = text.replace(anchor, helper + anchor, 1)
    print("added helper")
else:
    print("helper exists")

old = '''    caps = {
        "intro": (5.5 * scale_ratio, 8.0 * scale_ratio),
        "code": (9.0 * scale_ratio, 14.0 * scale_ratio),
        "execution": (5.5 * scale_ratio, 8.0 * scale_ratio),
        "terminal": (4.0 * scale_ratio, 6.0 * scale_ratio),
        "summary": (4.0 * scale_ratio, 6.0 * scale_ratio),
    }'''
new = '''    caps = {
        "intro": (5.5 * scale_ratio, 8.0 * scale_ratio),
        "concept": (10.0 * scale_ratio, 16.0 * scale_ratio),
        "code": (9.0 * scale_ratio, 14.0 * scale_ratio),
        "execution": (5.5 * scale_ratio, 8.0 * scale_ratio),
        "terminal": (4.0 * scale_ratio, 6.0 * scale_ratio),
        "summary": (4.0 * scale_ratio, 6.0 * scale_ratio),
    }'''
if old in text:
    text = text.replace(old, new, 1)
    print("added concept caps")
else:
    print("caps already patched or changed")

# After building updated list in _fit_reel_durations, rescale segments
marker = "    return lesson.model_copy(update={\"scenes\": updated})\n\n\ndef rewrite_reel_script"
# Actually the return is at end of _fit_reel_durations - find unique block
old_ret = '''    if abs(fitted_total - target) > 0.8:
        nudge = target / fitted_total
        updated = [
            scene.model_copy(
                update={"duration": round(max(min_spoken, min(max_spoken, scene.duration * nudge)), 1)}
            )
            for scene in updated
        ]
    return lesson.model_copy(update={"scenes": updated})
'''
new_ret = '''    if abs(fitted_total - target) > 0.8:
        nudge = target / fitted_total
        updated = [
            scene.model_copy(
                update={"duration": round(max(min_spoken, min(max_spoken, scene.duration * nudge)), 1)}
            )
            for scene in updated
        ]
    # Keep cue clocks aligned with fitted durations (avoids 34s segments on a 19s scene).
    updated = [_rescale_scene_segments(scene, float(scene.duration)) for scene in updated]
    return lesson.model_copy(update={"scenes": updated})
'''
if old_ret in text:
    text = text.replace(old_ret, new_ret, 1)
    print("rescale on fit")
elif "_rescale_scene_segments(scene, float(scene.duration))" in text:
    print("rescale already wired")
else:
    raise SystemExit("fit return block not found")

path.write_text(text)
ast.parse(text)
print("orchestrator ok")
