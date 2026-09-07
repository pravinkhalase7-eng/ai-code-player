#!/usr/bin/env python3
"""Backend visual synthesis + thumbnail viral bump + reelExport synthesize."""
from pathlib import Path
import re

ROOT = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder")

# ---------------------------------------------------------------------------
# reelExport: use synthesizeBoardSteps
# ---------------------------------------------------------------------------
ex = ROOT / "frontend/lib/reelExport.ts"
et = ex.read_text(encoding="utf-8")
old = '''  const steps = (scene.diagram_steps || [])
    .map((s) => ({
      title: String(s.title || "").trim(),
      detail: String(s.detail || "").trim(),
      example: String((s as { example?: string }).example || "").trim(),
    }))
    .filter((s) => s.title);
  const bullets = steps.length
    ? steps.map((s) => s.title)
    : (scene.bullets || []).map((b) => String(b || "").trim()).filter(Boolean);
'''
new = '''  const steps = lesson
    ? synthesizeBoardSteps(scene, lesson)
    : (scene.diagram_steps || [])
        .map((s) => ({
          title: String(s.title || "").trim(),
          detail: String(s.detail || "").trim(),
          example: String((s as { example?: string }).example || "").trim(),
        }))
        .filter((s) => s.title);
  const bullets = steps.length
    ? steps.map((s) => s.title)
    : (scene.bullets || []).map((b) => String(b || "").trim()).filter(Boolean);
'''
if old not in et:
    raise SystemExit("reelExport steps block missing")
et = et.replace(old, new, 1)
# Also treat intro/summary as explainer motion in label
et = et.replace(
    'ctx.fillText(explainer ? "EXPLAINER" : "EXPLAIN", WIDTH / 2, 88);',
    'const motionLabel = scene.type === "intro" ? "HOOK" : scene.type === "summary" ? "TAKEAWAY" : explainer ? "EXPLAINER" : "EXPLAIN";\n'
    '  ctx.fillText(motionLabel, WIDTH / 2, 88);',
    1,
)
ex.write_text(et, encoding="utf-8")
print("reelExport synthesize ok")

# ---------------------------------------------------------------------------
# Backend orchestrator: fill visual for explainer/info scenes
# ---------------------------------------------------------------------------
orch = ROOT / "backend/app/agents/orchestrator.py"
ot = orch.read_text(encoding="utf-8")

helper = '''
def _synth_visual_for_scene(scene, lesson) -> dict:
    """Fill VisualSpec so explainer/info never ship kind=none with empty callouts."""
    from app.schemas.lesson import VisualSpec

    existing = getattr(scene, "visual", None)
    kind = getattr(existing, "kind", None) if existing is not None else None
    callouts = list(getattr(existing, "callouts", None) or []) if existing is not None else []
    title = (getattr(existing, "title", None) or "") if existing is not None else ""
    if kind and kind != "none" and callouts:
        return {}

    st = getattr(scene, "type", None)
    topic = getattr(lesson, "topic", "") or getattr(lesson, "title", "") or "Concept"

    if not callouts:
        steps = list(getattr(scene, "diagram_steps", None) or [])
        if steps:
            callouts = [
                str(getattr(s, "title", None) or (s.get("title") if isinstance(s, dict) else s) or "")[:120]
                for s in steps
            ]
            callouts = [c for c in callouts if c.strip()]
        if not callouts:
            callouts = [str(b)[:120] for b in (getattr(scene, "bullets", None) or []) if str(b).strip()]
        if not callouts:
            callouts = [str(t)[:120] for t in (getattr(scene, "takeaways", None) or []) if str(t).strip()]
        if not callouts:
            segs = list(getattr(scene, "segments", None) or [])
            for seg in segs[:6]:
                text = getattr(seg, "text", None) if not isinstance(seg, dict) else seg.get("text")
                text = str(text or "").strip()
                if text:
                    callouts.append(text.split(".")[0][:72])
        if not callouts:
            narr = str(getattr(scene, "narration", "") or "").strip()
            parts = [p.strip() for p in narr.replace("!", ".").replace("?", ".").split(".") if len(p.strip()) > 12]
            callouts = [p[:72] for p in parts[:4]]

    if st == "intro":
        new_kind = "hook"
        title = title or f"Hook · {topic}"[:80]
    elif st == "summary":
        new_kind = "takeaway"
        title = title or f"Takeaway · {topic}"[:80]
    elif st == "concept":
        new_kind = "board" if list(getattr(scene, "diagram_steps", None) or []) else "bullets"
        title = title or f"{topic}"[:80]
    else:
        new_kind = kind if kind and kind != "none" else "board"
        title = title or topic[:80]

    if not callouts:
        callouts = [topic[:72], "Watch the stages", "Save this short"]

    return {
        "visual": VisualSpec(
            kind=new_kind or "board",
            title=title[:120],
            callouts=callouts[:8],
            particles=True,
        )
    }


'''

if "_synth_visual_for_scene" not in ot:
    # insert before _normalize_reel
    anchor = "def _normalize_reel(lesson: Lesson) -> Lesson:"
    if anchor not in ot:
        raise SystemExit("_normalize_reel missing")
    ot = ot.replace(anchor, helper + anchor, 1)
    print("inserted _synth_visual_for_scene")
else:
    print("synth helper already present")

# Wire into explain cleanup loop — after hashmap block, before cleaned.append
needle = '''                        patch["visual_diagram"] = HashMapVisual.model_validate(default_hashmap_visual())
            cleaned.append(scene.model_copy(update=patch) if patch else scene)
'''
# More flexible: find the cleaned.append inside explain block
if "patch.update(_synth_visual_for_scene" not in ot:
    # After the concept hashmap block ends, before cleaned.append for all scenes in explain
    old_append = "            cleaned.append(scene.model_copy(update=patch) if patch else scene)\n        scenes = cleaned"
    if old_append not in ot:
        raise SystemExit("cleaned.append block missing")
    new_append = (
        "            # Always fill visual payloads for explainer/info so runtime never sees kind=none blanks.\n"
        "            vis_patch = _synth_visual_for_scene(scene, lesson)\n"
        "            if vis_patch:\n"
        "                patch.update(vis_patch)\n"
        "            cleaned.append(scene.model_copy(update=patch) if patch else scene)\n"
        "        scenes = cleaned"
    )
    ot = ot.replace(old_append, new_append, 1)
    print("wired visual synth into normalize")
else:
    print("visual synth already wired")

orch.write_text(ot, encoding="utf-8")
print("orchestrator ok")

# ---------------------------------------------------------------------------
# Planner: ask for visual.kind + callouts
# ---------------------------------------------------------------------------
tm = ROOT / "backend/app/agents/topic_mode.py"
tt = tm.read_text(encoding="utf-8")
marker = '- Summary ({span(4, 6)}): One punchy takeaway about the mechanism. 2-3 short takeaways. Ask them to follow / save / comment.'
visual_rule = '''- EVERY scene MUST fill visual: {{"kind": "...", "title": "...", "callouts": [...], "particles": true}}.
  Never leave visual.kind as "none" or callouts empty.
  - intro.visual.kind = "hook"; callouts = 2-3 short cold-open phrases (misconception → twist).
  - concept.visual.kind = "board"; callouts = diagram_steps titles (same order).
  - summary.visual.kind = "takeaway"; callouts = the takeaways list.
- Summary ({span(4, 6)}): One punchy takeaway about the mechanism. 2-3 short takeaways. Ask them to follow / save / comment.'''
if 'visual.kind = "hook"' not in tt:
    if marker not in tt:
        raise SystemExit("summary marker missing in topic_mode")
    tt = tt.replace(marker, visual_rule, 1)
    tm.write_text(tt, encoding="utf-8")
    print("topic_mode visual rules ok")
else:
    print("topic_mode already has visual rules")

# Also info reel planner if present
if "def explain_reel_planner_instruction" in tt and 'info.visual' not in tt and 'kind = "hook"' in tt:
    # already updated explainer; try info planner
    info_marker = "Do NOT invent fake code"
    print("topic_mode explainer updated")

# ---------------------------------------------------------------------------
# Thumbnail: bump version + python why-learn metaphor
# ---------------------------------------------------------------------------
th = ROOT / "backend/app/services/images/thumbnail.py"
tht = th.read_text(encoding="utf-8")

if 'THUMB_VERSION = "tilt-v14-brand"' in tht:
    tht = tht.replace('THUMB_VERSION = "tilt-v14-brand"', 'THUMB_VERSION = "tilt-v15-viral"', 1)
    print("THUMB_VERSION -> tilt-v15-viral")
elif 'THUMB_VERSION = "tilt-v15-viral"' in tht:
    print("THUMB_VERSION already v15")
else:
    # bump whatever is there
    tht2, n = re.subn(
        r'THUMB_VERSION = "[^"]+"',
        'THUMB_VERSION = "tilt-v15-viral"',
        tht,
        count=1,
    )
    if not n:
        raise SystemExit("THUMB_VERSION not found")
    tht = tht2
    print("THUMB_VERSION forced to v15")

# Seed bump so posters regenerate differently
tht = tht.replace(
    'seed = int(hashlib.sha256(f"{headline}|explainer|v9|{spoken_language or \'\'}".encode()).hexdigest()[:8], 16)',
    'seed = int(hashlib.sha256(f"{headline}|explainer|v15|{spoken_language or \'\'}".encode()).hexdigest()[:8], 16)',
    1,
)

# Better hooks for python / why-learn
old_hooks_en = '''        hooks = [
            ("WAIT!", "Most beginners get this wrong"),
            ("OMG", "This diagram makes it click"),
            ("STOP!", "Learn this in 60 seconds"),
            ("WOW", "The missing mental model"),
            ("HOOK", "Save this before you code"),
        ]
        if re.search(r"hash\\s*map|hashtable", blob):
'''
new_hooks_en = '''        hooks = [
            ("WAIT!", "Most beginners get this wrong"),
            ("OMG", "This diagram makes it click"),
            ("STOP!", "Learn this in 60 seconds"),
            ("WOW", "The missing mental model"),
            ("HOOK", "Save this before you code"),
        ]
        if re.search(r"why\\s*learn\\s*python|learn\\s*python|python\\s*\\?", blob) or (
            "python" in blob and re.search(r"why|should|beginner|start", blob)
        ):
            hooks = [
                ("WAIT!", "Python looks easy… until this"),
                ("WHY?", "1 language → AI, web, jobs"),
                ("OMG", "English-like code that ships"),
                ("STOP!", "The real reason pros pick Python"),
            ]
        if re.search(r"hash\\s*map|hashtable", blob):
'''
if "why\\s*learn\\s*python" not in tht and "WAIT!\", \"Python looks easy" not in tht:
    if old_hooks_en not in tht:
        raise SystemExit("english hooks block missing")
    tht = tht.replace(old_hooks_en, new_hooks_en, 1)
    print("python why-learn hooks ok")
else:
    print("python hooks already present")

# diagram kind for python why
old_kind = '''def _diagram_kind(topic: str, reel_mode: str | None = None) -> str:
    blob = f"{topic or ''} {reel_mode or ''}".lower()
    if re.search(r"hash\\s*map|hashtable|hash\\s*table", blob):
        return "hashmap"
    if re.search(r"garbage|garbege|\\bgc\\b|heap|mark\\s*[- ]?\\s*sweep|collector", blob):
        return "gc"
    if re.search(r"generic|type\\s*parameter|<\\s*t\\s*>", blob):
        return "generics"
    if re.search(r"lambda|functional\\s*interface|->", blob):
        return "lambda"
    if (reel_mode or "").lower() in {"explainer", "info"} or not blob.strip():
        return "mechanism"
    return "mechanism"
'''
new_kind = '''def _diagram_kind(topic: str, reel_mode: str | None = None) -> str:
    blob = f"{topic or ''} {reel_mode or ''}".lower()
    if re.search(r"hash\\s*map|hashtable|hash\\s*table", blob):
        return "hashmap"
    if re.search(r"garbage|garbege|\\bgc\\b|heap|mark\\s*[- ]?\\s*sweep|collector", blob):
        return "gc"
    if re.search(r"why\\s*learn\\s*python|learn\\s*python|\\bpython\\b", blob) and re.search(
        r"why|learn|beginner|start|should|career|versatile", blob
    ):
        return "python_why"
    if re.search(r"generic|type\\s*parameter|<\\s*t\\s*>", blob):
        return "generics"
    if re.search(r"lambda|functional\\s*interface|->", blob):
        return "lambda"
    if (reel_mode or "").lower() in {"explainer", "info"} or not blob.strip():
        return "mechanism"
    return "mechanism"
'''
if "python_why" not in tht:
    if old_kind not in tht:
        raise SystemExit("diagram_kind missing")
    tht = tht.replace(old_kind, new_kind, 1)
    print("diagram_kind python_why ok")
else:
    print("python_why kind already present")

# Wire into _diagram_svg_v8
old_v8 = '''def _diagram_svg_v8(kind: str, topic: str, accent: str, glow: str, ink: str, seed: int, panel_w: int, panel_h: int) -> str:
    if kind == "hashmap":
        return _svg_hashmap_v8(accent, glow, ink, panel_w, panel_h)
    if kind == "gc":
        return _svg_gc_v8(accent, glow, ink, panel_w, panel_h)
    return _svg_mechanism_v8(accent, glow, ink, topic, panel_w, panel_h)
'''
new_v8 = '''def _diagram_svg_v8(kind: str, topic: str, accent: str, glow: str, ink: str, seed: int, panel_w: int, panel_h: int) -> str:
    if kind == "hashmap":
        return _svg_hashmap_v8(accent, glow, ink, panel_w, panel_h)
    if kind == "gc":
        return _svg_gc_v8(accent, glow, ink, panel_w, panel_h)
    if kind == "python_why":
        return _svg_python_why_v8(accent, glow, ink, topic, panel_w, panel_h)
    return _svg_mechanism_v8(accent, glow, ink, topic, panel_w, panel_h)
'''
if "_svg_python_why_v8" not in tht:
    if old_v8 not in tht:
        raise SystemExit("_diagram_svg_v8 missing")
    tht = tht.replace(old_v8, new_v8, 1)

    py_fn = '''
def _svg_python_why_v8(accent: str, glow: str, ink: str, topic: str, panel_w: int, panel_h: int) -> str:
    """Viral metaphor: readable syntax → multi-domain apps → career demand."""
    parts = [
        f'<text x="36" y="48" font-size="22" font-family="ui-sans-serif, system-ui" font-weight="800" '
        f'letter-spacing="4" fill="{accent}">WHY PYTHON?</text>',
        f'<text x="36" y="88" font-size="28" font-family="ui-sans-serif, system-ui" font-weight="700" fill="{ink}">'
        f'Reads like English → ships everywhere</text>',
    ]
    cards = [
        ("1", "Syntax", "print(\\"Hi\\")", accent),
        ("2", "Domains", "AI · Web · Auto", glow),
        ("3", "Demand", "Jobs + community", "#a3e635"),
    ]
    card_w = min(260, (panel_w - 72 - 40) // 3)
    gap = 20
    total = 3 * card_w + 2 * gap
    start = 36 + max(0, (panel_w - 72 - total) // 2)
    cy = 150
    ch = min(320, max(220, panel_h - 280))
    for i, (num, title, sub, color) in enumerate(cards):
        x = start + i * (card_w + gap)
        parts.append(
            f'<rect x="{x}" y="{cy}" width="{card_w}" height="{ch}" rx="28" fill="#020617" '
            f'stroke="{color}" stroke-width="3" filter="url(#softGlow)"/>'
            f'<circle cx="{x + 36}" cy="{cy + 40}" r="22" fill="{color}"/>'
            f'<text x="{x + 36}" y="{cy + 48}" text-anchor="middle" font-size="22" font-family="ui-sans-serif, system-ui" '
            f'font-weight="900" fill="#18181b">{num}</text>'
            f'<text x="{x + card_w/2}" y="{cy + 120}" text-anchor="middle" font-size="28" '
            f'font-family="ui-sans-serif, system-ui" font-weight="800" fill="{ink}">{html.escape(title)}</text>'
            f'<text x="{x + card_w/2}" y="{cy + 168}" text-anchor="middle" font-size="20" '
            f'font-family="{_MONO}" font-weight="700" fill="{color}">{html.escape(sub)}</text>'
        )
        if i < 2:
            ax = x + card_w + 4
            parts.append(
                f'<path d="M{ax} {cy + ch/2} h{gap - 8}" stroke="{accent}" stroke-width="4" stroke-linecap="round"/>'
                f'<polygon points="{ax + gap - 8},{cy + ch/2 - 8} {ax + gap + 4},{cy + ch/2} {ax + gap - 8},{cy + ch/2 + 8}" fill="{glow}"/>'
            )
    parts.append(
        f'<text x="36" y="{cy + ch + 70}" font-size="24" font-family="ui-sans-serif, system-ui" font-weight="700" '
        f'fill="{glow}">Beginner-friendly · Production-ready · High CTR topic</text>'
    )
    return "".join(parts)


'''
    # insert before _svg_mechanism_v8
    anchor = "def _svg_mechanism_v8("
    if anchor not in tht:
        raise SystemExit("mechanism_v8 missing")
    tht = tht.replace(anchor, py_fn + anchor, 1)
    print("python_why diagram ok")
else:
    print("python_why diagram already present")

th.write_text(tht, encoding="utf-8")
print("thumbnail.py ok")
print("DONE v2")
