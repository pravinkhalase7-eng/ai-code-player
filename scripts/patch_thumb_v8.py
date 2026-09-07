from pathlib import Path
import json
import sqlite3
import sys
import subprocess

ROOT = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder")
thumb = ROOT / "backend/app/services/images/thumbnail.py"
text = thumb.read_text()

# Bump version hard
text = text.replace('THUMB_VERSION = "diagram-v7-explainer"', 'THUMB_VERSION = "diagram-v8-hero"')
text = text.replace('THUMB_VERSION = "diagram-v8-hero"', 'THUMB_VERSION = "diagram-v8-hero"')

# Replace diagram helpers with richer layouts + explainer-specific poster layout
# Find and replace _svg_gc_diagram, _svg_hashmap_diagram, _svg_mechanism_diagram, and write_svg_poster explainer path

# Simpler approach: rewrite write_svg_poster to call a dedicated explainer poster writer
if "def write_explainer_svg_poster" not in text:
    insert_before = "def write_svg_poster("
    explainer_fn = r'''
def write_explainer_svg_poster(
    dest: Path,
    topic: str,
    title: str,
    language: str,
    reel_mode: str | None = None,
) -> Path:
    """Full-bleed 9:16 explainer poster with a large topic diagram (not a tiny footer card)."""
    mode = (reel_mode or "explainer").strip().lower() or "explainer"
    accent = "#22d3ee"
    glow = "#fbbf24"
    ink = "#ecfeff"
    headline = strip_duration_copy(title) or strip_duration_copy(topic) or topic or "Explainer"
    lines = _wrap(headline, 16, 3)
    seed = int(hashlib.sha256(f"{headline}|explainer|v8".encode()).hexdigest()[:8], 16)
    kind = _diagram_kind(topic, mode)
    badge = "EXPLAINER" if mode != "info" else "INFO REEL"

    title_svg = []
    y = 280
    for line in lines:
        title_svg.append(
            f'<text x="72" y="{y}" font-size="78" font-family="ui-sans-serif, system-ui, sans-serif" '
            f'font-weight="800" fill="{ink}">{html.escape(line)}</text>'
        )
        y += 92

    # Large diagram panel
    panel_top = min(max(y + 40, 560), 720)
    panel_h = 1920 - panel_top - 220
    diagram = _diagram_svg_v8(kind, topic, accent, glow, ink, seed, panel_w=936, panel_h=panel_h)

    dest.write_text(
        f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 1920" width="1080" height="1920">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#020617"/>
      <stop offset="55%" stop-color="#083344"/>
      <stop offset="100%" stop-color="#042f2e"/>
    </linearGradient>
    <linearGradient id="panel" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#082f49" stop-opacity="0.95"/>
      <stop offset="100%" stop-color="#042f2e" stop-opacity="0.92"/>
    </linearGradient>
    <filter id="softGlow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="8" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <rect width="1080" height="1920" fill="url(#bg)"/>
  <circle cx="920" cy="180" r="260" fill="{glow}" fill-opacity="0.16"/>
  <circle cx="120" cy="1680" r="300" fill="{accent}" fill-opacity="0.14"/>
  <circle cx="860" cy="1100" r="180" fill="{accent}" fill-opacity="0.08"/>
  <rect x="72" y="96" rx="28" width="360" height="72" fill="#fff"/>
  <text x="252" y="144" text-anchor="middle" font-size="28" font-family="ui-sans-serif, system-ui" font-weight="800" fill="#18181b">TECHSHALA</text>
  <text x="72" y="230" font-size="26" font-family="ui-sans-serif, system-ui" letter-spacing="8" fill="{accent}">{html.escape(badge)}</text>
  {"".join(title_svg)}
  <rect x="72" y="{panel_top}" rx="32" width="936" height="{panel_h}" fill="url(#panel)" stroke="{accent}" stroke-opacity="0.35" stroke-width="2"/>
  <rect x="72" y="{panel_top}" width="14" height="{panel_h}" rx="7" fill="{glow}"/>
  <g transform="translate(72, {panel_top})">{diagram}</g>
  <text x="72" y="1760" font-size="30" font-family="ui-sans-serif, system-ui" fill="{accent}">@techshalabypavi</text>
  <text x="72" y="1820" font-size="24" font-family="ui-sans-serif, system-ui" letter-spacing="4" fill="#a1a1aa">AI CODING TUTOR</text>
</svg>
""",
        encoding="utf-8",
    )
    return dest


def _diagram_svg_v8(kind: str, topic: str, accent: str, glow: str, ink: str, seed: int, panel_w: int, panel_h: int) -> str:
    if kind == "hashmap":
        return _svg_hashmap_v8(accent, glow, ink, panel_w, panel_h)
    if kind == "gc":
        return _svg_gc_v8(accent, glow, ink, panel_w, panel_h)
    return _svg_mechanism_v8(accent, glow, ink, topic, panel_w, panel_h)


def _svg_gc_v8(accent: str, glow: str, ink: str, panel_w: int, panel_h: int) -> str:
    # Roots row + heap objects + phase rail — fills the panel
    parts = [
        f'<text x="36" y="48" font-size="22" font-family="ui-sans-serif, system-ui" font-weight="800" '
        f'letter-spacing="4" fill="{accent}">GC · MARK &amp; SWEEP</text>',
        f'<text x="36" y="84" font-size="28" font-family="ui-sans-serif, system-ui" font-weight="700" fill="{ink}">'
        f'Roots keep objects alive</text>',
    ]
    # roots
    roots = [("stack", 36), ("static", 220), ("JNI", 404)]
    for label, x in roots:
        parts.append(
            f'<rect x="{x}" y="110" width="150" height="54" rx="16" fill="#022c22" stroke="{glow}" stroke-width="2"/>'
            f'<text x="{x + 75}" y="145" text-anchor="middle" font-size="20" font-family="ui-sans-serif, system-ui" '
            f'font-weight="800" fill="{glow}">{label}</text>'
        )
    # arrows down
    for _, x in roots[:2]:
        parts.append(
            f'<path d="M{x + 75} 164 V210" stroke="{accent}" stroke-width="3" stroke-dasharray="6 6"/>'
            f'<polygon points="{x + 75},218 {x + 68},204 {x + 82},204" fill="{accent}"/>'
        )
    # heap box
    heap_top = 230
    heap_h = min(420, panel_h - heap_top - 160)
    parts.append(
        f'<rect x="36" y="{heap_top}" width="{panel_w - 72}" height="{heap_h}" rx="24" fill="#020617" '
        f'stroke="{accent}" stroke-opacity="0.4" stroke-width="2"/>'
        f'<text x="56" y="{heap_top + 36}" font-size="18" font-family="ui-sans-serif, system-ui" font-weight="800" '
        f'letter-spacing="3" fill="{glow}">HEAP</text>'
    )
    objs = [
        ("A", True, "#f97316"),
        ("B", True, "#22d3ee"),
        ("C", True, "#a78bfa"),
        ("D", False, "#71717a"),
        ("E", False, "#52525b"),
    ]
    gap = 24
    box = 118
    total_w = 5 * box + 4 * gap
    start_x = 36 + max(20, ((panel_w - 72) - total_w) // 2)
    oy = heap_top + 70
    for i, (oid, live, color) in enumerate(objs):
        x = start_x + i * (box + gap)
        if live:
            parts.append(
                f'<rect x="{x}" y="{oy}" width="{box}" height="{box}" rx="22" fill="#14532d" stroke="#a3e635" '
                f'stroke-width="4" filter="url(#softGlow)"/>'
                f'<text x="{x + box/2}" y="{oy + 52}" text-anchor="middle" font-size="36" font-family="{_MONO}" '
                f'font-weight="800" fill="#fff">{oid}</text>'
                f'<text x="{x + box/2}" y="{oy + 84}" text-anchor="middle" font-size="16" font-family="ui-sans-serif, system-ui" '
                f'font-weight="800" fill="#bef264">MARKED</text>'
            )
        else:
            parts.append(
                f'<rect x="{x}" y="{oy}" width="{box}" height="{box}" rx="22" fill="#18181b" stroke="#52525b" '
                f'stroke-width="2" stroke-dasharray="6 5" opacity="0.75"/>'
                f'<text x="{x + box/2}" y="{oy + 52}" text-anchor="middle" font-size="36" font-family="{_MONO}" '
                f'font-weight="800" fill="#71717a">{oid}</text>'
                f'<text x="{x + box/2}" y="{oy + 84}" text-anchor="middle" font-size="16" font-family="ui-sans-serif, system-ui" '
                f'font-weight="700" fill="#a1a1aa">sweep</text>'
            )
    # phase rail
    phases = [("1 Allocate", False), ("2 Unref", False), ("3 Mark", True), ("4 Sweep", False), ("5 Compact", False)]
    py = heap_top + heap_h + 36
    pw = (panel_w - 72 - 4 * 12) // 5
    for i, (label, on) in enumerate(phases):
        x = 36 + i * (pw + 12)
        parts.append(
            f'<rect x="{x}" y="{py}" width="{pw}" height="56" rx="18" fill="{("#854d0e" if on else "#0f172a")}" '
            f'stroke="{glow if on else accent}" stroke-width="{3 if on else 1.5}" fill-opacity="0.85"/>'
            f'<text x="{x + pw/2}" y="{py + 36}" text-anchor="middle" font-size="16" font-family="ui-sans-serif, system-ui" '
            f'font-weight="800" fill="{("#fef3c7" if on else ink)}">{html.escape(label)}</text>'
        )
    parts.append(
        f'<text x="36" y="{py + 96}" font-size="22" font-family="ui-sans-serif, system-ui" fill="#a1a1aa">'
        f'Live graph stays · unreachable memory is freed</text>'
    )
    return "".join(parts)


def _svg_hashmap_v8(accent: str, glow: str, ink: str, panel_w: int, panel_h: int) -> str:
    parts = [
        f'<text x="36" y="48" font-size="22" font-family="ui-sans-serif, system-ui" font-weight="800" '
        f'letter-spacing="4" fill="{accent}">HASHMAP · INTERNALS</text>',
        f'<text x="36" y="88" font-size="28" font-family="ui-sans-serif, system-ui" font-weight="700" fill="{ink}">'
        f'hash → index → node · chain on collision</text>',
        f'<text x="36" y="130" font-size="20" font-family="{_MONO}" fill="{glow}">index = hash &amp; (n - 1)</text>',
    ]
    fills = {
        1: [("Mia", "100", "#f97316"), ("Zoe", "300", glow)],
        5: [("Leo", "200", "#38bdf8")],
    }
    row_h = 58
    start_y = 160
    for b in range(8):
        by = start_y + b * row_h
        active = b in fills
        parts.append(
            f'<rect x="36" y="{by}" width="70" height="46" rx="12" fill="{"#083344" if active else "#020617"}" '
            f'stroke="{accent if active else "#334155"}" stroke-width="2"/>'
            f'<text x="71" y="{by + 30}" text-anchor="middle" font-size="20" font-family="{_MONO}" font-weight="800" '
            f'fill="{ink if active else "#64748b"}">{b}</text>'
        )
        chain = fills.get(b) or []
        nx = 130
        for i, (key, val, color) in enumerate(chain):
            parts.append(
                f'<rect x="{nx}" y="{by - 2}" width="200" height="50" rx="14" fill="#020617" stroke="{color}" stroke-width="3"/>'
                f'<text x="{nx + 16}" y="{by + 20}" font-size="20" font-family="{_MONO}" font-weight="800" fill="#fff">{html.escape(key)}</text>'
                f'<text x="{nx + 16}" y="{by + 40}" font-size="15" font-family="{_MONO}" fill="#94a3b8">val {html.escape(val)}  next{" →" if i < len(chain)-1 else " ∅"}</text>'
            )
            if i < len(chain) - 1:
                parts.append(
                    f'<path d="M{nx + 200} {by + 23} H{nx + 226}" stroke="{glow}" stroke-width="4"/>'
                    f'<polygon points="{nx + 226},{by + 16} {nx + 242},{by + 23} {nx + 226},{by + 30}" fill="{glow}"/>'
                )
            nx += 250
    return "".join(parts)


def _svg_mechanism_v8(accent: str, glow: str, ink: str, topic: str, panel_w: int, panel_h: int) -> str:
    steps = ["Idea", "Break it", "Trace", "Result"]
    low = (topic or "").lower()
    if "generic" in low:
        steps = ["Type", "Param", "Bound", "Use"]
    elif "lambda" in low:
        steps = ["Iface", "Args", "Body", "Call"]
    parts = [
        f'<text x="36" y="48" font-size="22" font-family="ui-sans-serif, system-ui" font-weight="800" '
        f'letter-spacing="4" fill="{accent}">HOW IT WORKS</text>',
        f'<text x="36" y="92" font-size="30" font-family="ui-sans-serif, system-ui" font-weight="700" fill="{ink}">'
        f'{html.escape((topic or "Concept")[:42])}</text>',
    ]
    n = len(steps)
    usable = panel_w - 72
    for i, label in enumerate(steps):
        x = 36 + i * (usable / n) + (usable / n) / 2
        on = i == 1
        parts.append(
            f'<circle cx="{x}" cy="260" r="58" fill="#020617" stroke="{glow if on else accent}" '
            f'stroke-width="{5 if on else 2}" filter="url(#softGlow)"/>'
            f'<text x="{x}" y="270" text-anchor="middle" font-size="22" font-family="ui-sans-serif, system-ui" '
            f'font-weight="800" fill="{ink}">{html.escape(label)}</text>'
        )
        if i < n - 1:
            x2 = 36 + (i + 1) * (usable / n) + (usable / n) / 2
            parts.append(
                f'<path d="M{x + 66} 260 H{x2 - 66}" stroke="{accent}" stroke-width="5" stroke-linecap="round" opacity="0.55"/>'
            )
    return "".join(parts)

'''
    text = text.replace(insert_before, explainer_fn + insert_before, 1)

# Patch write_svg_poster to delegate explainers
old = '''def write_svg_poster(
    dest: Path,
    topic: str,
    title: str,
    language: str,
    code: str | None = None,
    *,
    reel_mode: str | None = None,
) -> Path:
    lang = _normalize_lang(language)
    colors = PALETTES.get(lang, PALETTES["java"])
    mode = (reel_mode or "").strip().lower()
    if mode in {"explainer", "info"}:
        # Cyan explainer look (matches MechanismBoard / Explainer UI)
        colors = {
            "bg0": "#031018",
            "bg1": "#083344",
            "accent": "#22d3ee",
            "glow": "#fbbf24",
            "ink": "#ecfeff",
        }
'''
new = '''def write_svg_poster(
    dest: Path,
    topic: str,
    title: str,
    language: str,
    code: str | None = None,
    *,
    reel_mode: str | None = None,
) -> Path:
    mode = (reel_mode or "").strip().lower()
    if mode in {"explainer", "info"}:
        return write_explainer_svg_poster(dest, topic, title, language, reel_mode=mode)
    lang = _normalize_lang(language)
    colors = PALETTES.get(lang, PALETTES["java"])
'''
if old not in text:
    # maybe already partially different - try softer match
    if "return write_explainer_svg_poster" in text:
        print("already delegates")
    else:
        raise SystemExit("write_svg_poster head not found for patch")
else:
    text = text.replace(old, new, 1)

# Fix badge line still referencing mode in non-explainer path - the old badge used mode which may be unset
# In non-explainer path mode is still set above. Good.

# ensure_reel_thumbnail: unique cache buster with content hash
old_ensure_tail = '''    write_svg_poster(
        svg_path, topic, poster_title, language, code, reel_mode=reel_mode
    )
    return f"/images/{svg_path.name}?v={THUMB_VERSION}"
'''
new_ensure_tail = '''    write_svg_poster(
        svg_path, topic, poster_title, language, code, reel_mode=reel_mode
    )
    # Content hash so browsers cannot keep an old SVG under the same filename.
    digest = hashlib.sha256(svg_path.read_bytes()).hexdigest()[:10]
    return f"/images/{svg_path.name}?v={THUMB_VERSION}-{digest}"
'''
if old_ensure_tail not in text:
    raise SystemExit("ensure tail not found")
text = text.replace(old_ensure_tail, new_ensure_tail, 1)

thumb.write_text(text)
print("thumbnail.py patched v8")

# Syntax check + regenerate
sys.path.insert(0, str(ROOT / "backend"))
from importlib import reload
import app.services.images.thumbnail as th
reload(th)

con = sqlite3.connect(ROOT / "backend/tutor.db")
for lid, raw in con.execute("select id, lesson_json from lessons").fetchall():
    p = json.loads(raw)
    if p.get("format") != "reel":
        continue
    mode = p.get("reel_mode")
    url = th.ensure_reel_thumbnail(
        p.get("lesson_id") or lid,
        p.get("topic") or "",
        p.get("topic") or p.get("title") or "",
        p.get("language") or "java",
        None,
        reel_mode=mode,
    )
    p["thumbnail_url"] = url
    p["thumbnail_custom"] = False
    con.execute("update lessons set lesson_json=? where id=?", (json.dumps(p, ensure_ascii=False), lid))
    print("regen", lid[:28], url)
con.commit()
con.close()

# Also try PNG sidecar via magick for dashboard reliability
for svg in (ROOT / "storage/images").glob("thumb_les_*.svg"):
    png = svg.with_suffix(".png")
    try:
        subprocess.run(
            ["magick", "-background", "none", str(svg), "-resize", "540x960", str(png)],
            check=True,
            capture_output=True,
            text=True,
        )
        print("png", png.name, png.stat().st_size)
    except Exception as e:
        print("png fail", svg.name, e)

print("done", th.THUMB_VERSION)
