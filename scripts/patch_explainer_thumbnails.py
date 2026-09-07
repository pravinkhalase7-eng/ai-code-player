from pathlib import Path
import sqlite3
import json
import re

ROOT = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder")
thumb = ROOT / "backend/app/services/images/thumbnail.py"

# Replace THUMB_VERSION and rewrite write_svg_poster + helpers + ensure signature
text = thumb.read_text()

# Bump version
text = text.replace('THUMB_VERSION = "code-v6-hero-line"', 'THUMB_VERSION = "diagram-v7-explainer"')

# Insert diagram helpers before write_svg_poster if missing
if "def _diagram_kind" not in text:
    helpers = r'''
def _diagram_kind(topic: str, reel_mode: str | None = None) -> str:
    blob = f"{topic or ''} {reel_mode or ''}".lower()
    if re.search(r"hash\s*map|hashtable|hash\s*table", blob):
        return "hashmap"
    if re.search(r"garbage|garbege|\bgc\b|heap|mark\s*[- ]?\s*sweep|collector", blob):
        return "gc"
    if re.search(r"generic|type\s*parameter|<\s*t\s*>", blob):
        return "generics"
    if re.search(r"lambda|functional\s*interface|->", blob):
        return "lambda"
    if (reel_mode or "").lower() in {"explainer", "info"} or not blob.strip():
        return "mechanism"
    return "mechanism"


def _svg_hashmap_diagram(accent: str, glow: str, ink: str, seed: int) -> str:
    """Mini whiteboard: buckets + chained nodes (YouTube-style HashMap)."""
    buckets = []
    # filled: 1 -> Mia->Zoe, 5 -> Leo
    fills = {1: [("Mia", "100", accent), ("Zoe", "300", glow)], 5: [("Leo", "200", "#38bdf8")]}
    y0 = 0
    for b in range(8):
        by = y0 + b * 52
        active = b in fills
        buckets.append(
            f'<rect x="0" y="{by}" width="56" height="40" rx="8" fill="{"#0e7490" if active else "#18181b"}" '
            f'stroke="{accent if active else "#3f3f46"}" stroke-width="2"/>'
            f'<text x="28" y="{by + 26}" text-anchor="middle" font-size="18" font-family="{_MONO}" '
            f'font-weight="800" fill="{ink if active else "#71717a"}">{b}</text>'
        )
        chain = fills.get(b) or []
        nx = 76
        for i, (key, val, color) in enumerate(chain):
            buckets.append(
                f'<rect x="{nx}" y="{by - 4}" width="150" height="48" rx="10" fill="#09090b" '
                f'stroke="{color}" stroke-width="2.5"/>'
                f'<text x="{nx + 12}" y="{by + 16}" font-size="16" font-family="{_MONO}" font-weight="800" fill="#fff">{html.escape(key)}</text>'
                f'<text x="{nx + 12}" y="{by + 34}" font-size="13" font-family="{_MONO}" fill="#a1a1aa">val {html.escape(val)} · next{"→" if i < len(chain)-1 else "∅"}</text>'
            )
            if i < len(chain) - 1:
                buckets.append(
                    f'<path d="M{nx + 150} {by + 20} H{nx + 168}" stroke="{glow}" stroke-width="3" fill="none"/>'
                    f'<polygon points="{nx + 168},{by + 14} {nx + 180},{by + 20} {nx + 168},{by + 26}" fill="{glow}"/>'
                )
            nx += 188
    return (
        f'<g transform="translate(36, 28)">'
        f'<text x="0" y="0" font-size="18" font-family="ui-sans-serif, system-ui" font-weight="800" '
        f'letter-spacing="3" fill="{accent}">HASHMAP · BUCKETS</text>'
        f'<g transform="translate(0, 24)">{"".join(buckets)}</g>'
        f'<text x="0" y="460" font-size="16" font-family="ui-sans-serif, system-ui" fill="#a1a1aa">'
        f'hash → index → node · collision chains via next</text>'
        f'</g>'
    )


def _svg_gc_diagram(accent: str, glow: str, ink: str) -> str:
    objs = [
        ("A", True, accent),
        ("B", True, "#22d3ee"),
        ("C", True, "#a78bfa"),
        ("D", False, "#71717a"),
        ("E", False, "#52525b"),
    ]
    cards = []
    for i, (oid, live, color) in enumerate(objs):
        x = 20 + (i % 5) * 110
        y = 40 + (0 if i < 5 else 120)
        mark = live
        cards.append(
            f'<rect x="{x}" y="{y}" width="96" height="96" rx="16" fill="{"#14532d" if mark else "#18181b"}" '
            f'stroke="{("#a3e635" if mark else color)}" stroke-width="{3 if mark else 2}" '
            f'fill-opacity="{0.55 if mark else 0.85}"/>'
            f'<text x="{x + 48}" y="{y + 42}" text-anchor="middle" font-size="28" font-family="{_MONO}" '
            f'font-weight="800" fill="#fff">{oid}</text>'
            f'<text x="{x + 48}" y="{y + 68}" text-anchor="middle" font-size="14" font-family="ui-sans-serif, system-ui" '
            f'fill="{("#bef264" if mark else "#a1a1aa")}">{"MARKED" if mark else "dead"}</text>'
        )
    phases = ["allocate", "unref", "mark", "sweep", "compact"]
    chips = []
    for i, ph in enumerate(phases):
        x = 20 + i * 118
        on = ph == "mark"
        chips.append(
            f'<rect x="{x}" y="170" width="108" height="34" rx="17" fill="{glow if on else "#18181b"}" '
            f'fill-opacity="{0.35 if on else 0.9}" stroke="{accent if on else "#3f3f46"}"/>'
            f'<text x="{x + 54}" y="192" text-anchor="middle" font-size="13" font-family="ui-sans-serif, system-ui" '
            f'font-weight="800" fill="{("#fff" if on else "#a1a1aa")}">{ph}</text>'
        )
    return (
        f'<g transform="translate(24, 20)">'
        f'<text x="0" y="0" font-size="18" font-family="ui-sans-serif, system-ui" font-weight="800" '
        f'letter-spacing="3" fill="{accent}">GC · HEAP</text>'
        f'{"".join(cards)}{"".join(chips)}'
        f'<text x="20" y="240" font-size="16" font-family="ui-sans-serif, system-ui" fill="#a1a1aa">'
        f'mark live objects · sweep the rest · compact</text>'
        f'</g>'
    )


def _svg_mechanism_diagram(accent: str, glow: str, ink: str, topic: str) -> str:
    steps = ["Idea", "Break", "Trace", "Result"]
    low = (topic or "").lower()
    if "generic" in low:
        steps = ["Type", "Param", "Bound", "Use"]
    elif "lambda" in low:
        steps = ["Iface", "Args", "Body", "Call"]
    elif "thread" in low:
        steps = ["Start", "Run", "Wait", "Join"]
    nodes = []
    for i, label in enumerate(steps):
        x = 40 + i * 200
        nodes.append(
            f'<circle cx="{x}" cy="90" r="42" fill="#09090b" stroke="{accent if i == 1 else glow}" '
            f'stroke-width="{4 if i == 1 else 2}" fill-opacity="0.85"/>'
            f'<text x="{x}" y="98" text-anchor="middle" font-size="18" font-family="ui-sans-serif, system-ui" '
            f'font-weight="800" fill="{ink}">{html.escape(label)}</text>'
        )
        if i < len(steps) - 1:
            nodes.append(
                f'<path d="M{x + 48} 90 H{x + 152}" stroke="{accent}" stroke-width="4" stroke-linecap="round" '
                f'opacity="0.55"/>'
                f'<polygon points="{x + 152},82 {x + 168},90 {x + 152},98" fill="{accent}" opacity="0.8"/>'
            )
    return (
        f'<g transform="translate(24, 36)">'
        f'<text x="0" y="0" font-size="18" font-family="ui-sans-serif, system-ui" font-weight="800" '
        f'letter-spacing="3" fill="{accent}">HOW IT WORKS</text>'
        f'<rect x="8" y="28" width="860" height="140" rx="24" fill="#09090b" fill-opacity="0.35" '
        f'stroke="{accent}" stroke-opacity="0.25"/>'
        f'{"".join(nodes)}'
        f'<text x="40" y="200" font-size="18" font-family="ui-sans-serif, system-ui" fill="#a1a1aa">'
        f'{html.escape((topic or "Concept")[:48])} · animated explainer</text>'
        f'</g>'
    )


def _diagram_svg(topic: str, reel_mode: str | None, accent: str, glow: str, ink: str, seed: int) -> str:
    kind = _diagram_kind(topic, reel_mode)
    if kind == "hashmap":
        return _svg_hashmap_diagram(accent, glow, ink, seed)
    if kind == "gc":
        return _svg_gc_diagram(accent, glow, ink)
    return _svg_mechanism_diagram(accent, glow, ink, topic)

'''
    marker = "def write_svg_poster("
    if marker not in text:
        raise SystemExit("write_svg_poster not found")
    text = text.replace(marker, helpers + marker, 1)

# Patch write_svg_poster signature and empty branch
old_sig = '''def write_svg_poster(
    dest: Path,
    topic: str,
    title: str,
    language: str,
    code: str | None = None,
) -> Path:'''
new_sig = '''def write_svg_poster(
    dest: Path,
    topic: str,
    title: str,
    language: str,
    code: str | None = None,
    *,
    reel_mode: str | None = None,
) -> Path:'''
if old_sig not in text:
    raise SystemExit("write_svg_poster sig not found")
text = text.replace(old_sig, new_sig, 1)

# Use cyan palette for explainers
old_colors = '''    lang = _normalize_lang(language)
    colors = PALETTES.get(lang, PALETTES["java"])
'''
new_colors = '''    lang = _normalize_lang(language)
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
if old_colors not in text:
    raise SystemExit("colors block not found")
text = text.replace(old_colors, new_colors, 1)

# Badge line: show EXPLAINER when relevant
old_badge = '''  <text x="72" y="240" font-size="26" font-family="ui-sans-serif, system-ui" letter-spacing="8" fill="{colors["accent"]}">{html.escape(lang.upper())}</text>
'''
new_badge = '''  <text x="72" y="240" font-size="26" font-family="ui-sans-serif, system-ui" letter-spacing="8" fill="{colors["accent"]}">{html.escape((mode.upper() if mode in {"explainer", "info"} else lang.upper()))}</text>
'''
if old_badge not in text:
    raise SystemExit("lang badge not found")
text = text.replace(old_badge, new_badge, 1)

# Replace empty preview with diagram; also use taller card for diagrams
old_preview_block = '''    preview = _preview_lines(lang, code, max_lines=max_rows)
    card_h = (row_h * max(len(preview), 1) + 88) if preview else 120
    if code_top + card_h > footer_top:
        card_h = max(120, footer_top - code_top)
    code_svg = []
    cy = code_top + 58
    # One hero teaching line in accent; every other line the same muted ink.
    hero = 0
    for index, row in enumerate(preview):
        stripped = row.strip()
        if not stripped or stripped in {"{", "}", "};"}:
            continue
        low = stripped.casefold()
        if low.startswith(("import ", "package ", "from ", "public class", "public static void main")):
            continue
        hero = index
        break
    if preview:
        for index, row in enumerate(preview):
            fill = colors["accent"] if index == hero else "#d4d4d8"
            formatted = _format_code_row(row)
            code_svg.append(
                f'<text x="108" y="{cy}" font-size="20" font-family="{_MONO}" fill="#52525b">'
                f"{index + 1:02d}</text>"
                f'<text x="160" y="{cy}" xml:space="preserve" font-size="24" font-family="{_MONO}" '
                f'fill="{fill}">{html.escape(formatted)}</text>'
            )
            cy += row_h
    else:
        code_svg.append(
            f'<text x="108" y="{cy}" font-size="28" font-family="ui-sans-serif, system-ui" '
            f'fill="#a1a1aa">Explain reel · concept only</text>'
        )
'''
new_preview_block = '''    preview = _preview_lines(lang, code, max_lines=max_rows)
    use_diagram = (not preview) or mode in {"explainer", "info"}
    # Explainers prefer diagram even if stub code leaked in
    if mode in {"explainer", "info"}:
        preview = []
        use_diagram = True
    card_h = (row_h * max(len(preview), 1) + 88) if preview else (520 if use_diagram else 120)
    if code_top + card_h > footer_top:
        card_h = max(120, footer_top - code_top)
    code_svg = []
    cy = code_top + 58
    # One hero teaching line in accent; every other line the same muted ink.
    hero = 0
    for index, row in enumerate(preview):
        stripped = row.strip()
        if not stripped or stripped in {"{", "}", "};"}:
            continue
        low = stripped.casefold()
        if low.startswith(("import ", "package ", "from ", "public class", "public static void main")):
            continue
        hero = index
        break
    if preview:
        for index, row in enumerate(preview):
            fill = colors["accent"] if index == hero else "#d4d4d8"
            formatted = _format_code_row(row)
            code_svg.append(
                f'<text x="108" y="{cy}" font-size="20" font-family="{_MONO}" fill="#52525b">'
                f"{index + 1:02d}</text>"
                f'<text x="160" y="{cy}" xml:space="preserve" font-size="24" font-family="{_MONO}" '
                f'fill="{fill}">{html.escape(formatted)}</text>'
            )
            cy += row_h
    elif use_diagram:
        code_svg.append(
            f'<g transform="translate(72, {code_top})">'
            f'{_diagram_svg(topic, mode, colors["accent"], colors["glow"], colors["ink"], seed)}'
            f'</g>'
        )
    else:
        code_svg.append(
            f'<text x="108" y="{cy}" font-size="28" font-family="ui-sans-serif, system-ui" '
            f'fill="#a1a1aa">Explain reel · concept only</text>'
        )
'''
if old_preview_block not in text:
    raise SystemExit("preview block not found")
text = text.replace(old_preview_block, new_preview_block, 1)

# When diagram is drawn outside the card rect (absolute translate includes card origin),
# the diagram is nested inside the card visually via transform from card top — but we also
# still draw the dark card rect. Diagram translate includes x=72 which double-offsets.
# Fix: diagram group should be relative to card (0,0) since parent already at code area.
# Actually write: transform translate(72, code_top) AND diagram has its own padding — but the
# card rect is at x=72 y=code_top, and code_svg is siblings inside SVG root. For code text,
# x=108 is absolute. For diagram I used translate(72, code_top) which matches card — good.
# Inner diagram starts at translate(36,28) relative — good.

old_ensure = '''def ensure_reel_thumbnail(
    lesson_id: str,
    topic: str,
    title: str,
    language: str,
    code: str | None = None,
) -> str:
    folder = images_dir()
    svg_path = folder / f"thumb_{lesson_id}.svg"
    poster_title = strip_duration_copy(topic) or strip_duration_copy(title) or topic
    write_svg_poster(svg_path, topic, poster_title, language, code)
    return f"/images/{svg_path.name}?v={THUMB_VERSION}"
'''
new_ensure = '''def ensure_reel_thumbnail(
    lesson_id: str,
    topic: str,
    title: str,
    language: str,
    code: str | None = None,
    *,
    reel_mode: str | None = None,
) -> str:
    folder = images_dir()
    svg_path = folder / f"thumb_{lesson_id}.svg"
    poster_title = strip_duration_copy(topic) or strip_duration_copy(title) or topic
    write_svg_poster(
        svg_path, topic, poster_title, language, code, reel_mode=reel_mode
    )
    return f"/images/{svg_path.name}?v={THUMB_VERSION}"
'''
if old_ensure not in text:
    raise SystemExit("ensure_reel_thumbnail not found")
text = text.replace(old_ensure, new_ensure, 1)

thumb.write_text(text)
print("thumbnail.py updated")

# Update call sites to pass reel_mode
svc = ROOT / "backend/app/services/lesson_service.py"
sv = svc.read_text()
sv2 = sv.replace(
    '''    url = ensure_reel_thumbnail(
        lesson.lesson_id, lesson.topic, lesson.topic, lesson.language, program
    )
''',
    '''    url = ensure_reel_thumbnail(
        lesson.lesson_id,
        lesson.topic,
        lesson.topic,
        lesson.language,
        program,
        reel_mode=getattr(lesson, "reel_mode", None),
    )
''',
)
sv2 = sv2.replace(
    '''                    "thumbnail_url": ensure_reel_thumbnail(
                        lesson.lesson_id,
                        lesson.topic,
                        lesson.topic,
                        lesson.language,
                        extract_primary_code(lesson.model_dump(mode="json"))[1],
                    )
''',
    '''                    "thumbnail_url": ensure_reel_thumbnail(
                        lesson.lesson_id,
                        lesson.topic,
                        lesson.topic,
                        lesson.language,
                        extract_primary_code(lesson.model_dump(mode="json"))[1],
                        reel_mode=getattr(lesson, "reel_mode", None),
                    )
''',
)
if sv2 == sv:
    print("WARNING: lesson_service call sites may already be patched or mismatched")
else:
    svc.write_text(sv2)
    print("lesson_service call sites updated")

# Regen thumbnails for all explainer/info lessons
from app.services.images.thumbnail import ensure_reel_thumbnail  # type: ignore

# Fix import path
import sys
sys.path.insert(0, str(ROOT / "backend"))
from app.services.images.thumbnail import ensure_reel_thumbnail, write_svg_poster, THUMB_VERSION

con = sqlite3.connect(ROOT / "backend" / "tutor.db")
rows = con.execute("select id, lesson_json from lessons").fetchall()
updated = 0
for lid, raw in rows:
    p = json.loads(raw)
    mode = p.get("reel_mode")
    if p.get("format") != "reel":
        continue
    url = ensure_reel_thumbnail(
        p.get("lesson_id") or lid,
        p.get("topic") or "",
        p.get("topic") or p.get("title") or "",
        p.get("language") or "java",
        None if mode in {"explainer", "info"} else None,
        reel_mode=mode,
    )
    if p.get("thumbnail_url") != url:
        p["thumbnail_url"] = url
        p["thumbnail_custom"] = False
        con.execute(
            "update lessons set lesson_json=? where id=?",
            (json.dumps(p, ensure_ascii=False), lid),
        )
        updated += 1
        print("regen", lid[:24], mode, url)
con.commit()
con.close()
print("THUMB_VERSION", THUMB_VERSION, "updated_rows", updated)
