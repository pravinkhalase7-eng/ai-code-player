from __future__ import annotations

import math
import hashlib
import html
import logging
import re
from pathlib import Path

from app.config import settings
from app.services.locale import strip_duration_copy

logger = logging.getLogger(__name__)

PALETTES = {
    "java": {
        "bg0": "#1a0f05",
        "bg1": "#431407",
        "accent": "#fb923c",
        "glow": "#f97316",
        "ink": "#ffedd5",
    },
    "python": {
        "bg0": "#07111f",
        "bg1": "#1e3a5f",
        "accent": "#38bdf8",
        "glow": "#facc15",
        "ink": "#e0f2fe",
    },
    "javascript": {
        "bg0": "#111105",
        "bg1": "#3f3f07",
        "accent": "#facc15",
        "glow": "#a3e635",
        "ink": "#fefce8",
    },
}

CODE_LINES = {
    "java": [
        "public class Main {",
        "    for (int i = 0; i < n; i++) {",
        "        System.out.println(i);",
        "    }",
        "}",
    ],
    "python": [
        "def main():",
        "    for i in range(n):",
        "        print(i)",
        "main()",
    ],
    "javascript": [
        "const run = async () => {",
        "    const value = await load();",
        "    console.log(value);",
        "};",
        "run();",
    ],
}

_MONO = "Menlo, Consolas, Monaco, ui-monospace, monospace"
THUMB_VERSION = "tilt-v15-viral"


def images_dir() -> Path:
    path = Path(settings.storage_path) / "images"
    path.mkdir(parents=True, exist_ok=True)
    return path



def thumbnail_prompt(
    topic: str,
    language: str,
    *,
    spoken_language: str | None = None,
    reel_mode: str | None = None,
) -> str:
    """High-CTR viral Shorts poster prompt (Gemini / image providers)."""
    topic_clean = strip_duration_copy(topic) or topic or "Coding"
    lang = (language or "java").strip().lower() or "java"
    mode = (reel_mode or "").strip().lower()
    spoken = (spoken_language or "en").strip().lower()
    hindi = spoken in {"hi", "hindi"} or spoken.startswith("hi")

    words = re.findall(r"[A-Za-z0-9+#]+", topic_clean)
    headline = " ".join(w.upper() for w in words[:4]) or lang.upper()
    if len(headline) > 28:
        headline = headline[:28].rstrip() + "…"

    if hindi:
        hooks = ["कौन सा?", "वाह!", "रुको!", "ये कैसे?", "सच??"]
    else:
        hooks = ["WHICH ONE?", "WAIT…", "MOST MISS THIS", "THIS OR THAT?", "WHY?"]
    seed = int(hashlib.sha256(f"{topic_clean}|{lang}|{mode}".encode()).hexdigest()[:8], 16)
    hook = hooks[seed % len(hooks)]

    blob = topic_clean.lower()
    if re.search(r"hash\s*map|hashtable", blob) and "collection" not in blob:
        visual = (
            "glowing HashMap whiteboard: vertical buckets, chained nodes, hash→index motion; "
            "neon put/collision energy"
        )
    elif re.search(r"garbage|\bgc\b|heap", blob):
        visual = (
            "glowing GC heap with live vs dead objects, mark & sweep energy beams, "
            "futuristic memory cleanup scene"
        )
    elif re.search(r"collection|arraylist|hashset|\bqueue\b|array\s*list", blob):
        visual = (
            "glowing Java logo in the upper-middle; surround it with large colorful floating "
            "data-structure cards labeled ArrayList, HashSet, HashMap, Queue; glowing data flowing "
            "between the structures (speed, complexity, organization)"
        )
    elif re.search(r"concurren|multithread|\bthreads?\b|synchronized|completable\s*future|\blocks?\b", blob):
        visual = (
            "glowing Java logo upper-middle; large floating neon cards labeled Thread, synchronized, "
            "Lock, CompletableFuture; parallel glowing lanes of work merging safely into shared data"
        )
    else:
        visual = (
            f"futuristic {lang} programming scene with a glowing language emblem upper-middle; "
            "large neon concept cards naming the real subtopics from the video title; light trails connecting them"
        )

    explain = "how-it-works explainer" if mode in {"explainer", "info"} else "coding short"

    return (
        f"Create a highly catchy, high-CTR vertical 9:16 thumbnail/poster for a programming video. "
        f"Topic: {topic_clean}. Language: {lang}. Format: {explain}. "
        f'Main headline in huge bold typography: "{headline}". '
        f'Curiosity hook in a smaller highly contrasting text box: "{hook}". '
        f"Visual: {visual}. "
        "Composition: put the logo/main visual in the upper-middle; put the headline near the center "
        "in huge bold type; put the curiosity hook in a contrasting box; keep important text away "
        "from extreme top and bottom edges; every element clear on a mobile phone; strong vertical "
        "visual flow; clean and uncluttered. "
        "Colors: dark black/navy background with Java red, orange, electric blue, and purple neon "
        "accents; glowing edges, dramatic highlights, shadows, and depth. "
        "Style: viral coding-content thumbnail, premium YouTube Shorts design, futuristic technology, "
        "cinematic lighting, bold 3D typography, neon glow, high contrast, sharp details, dynamic "
        "composition, professional graphic design, visually striking. "
        f'The thumbnail should communicate "{topic_clean} made simple" instantly while creating curiosity. '
        "Aspect ratio 9:16, resolution 1080×1920, mobile-first. "
        "No watermark, no unnecessary text, no clutter."
    )


def _wrap(text: str, width: int = 18, max_lines: int = 3) -> list[str]:
    words = (text or "").split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if len(trial) > width and current:
            lines.append(current)
            current = word
            if len(lines) >= max_lines:
                break
        else:
            current = trial
    if current and len(lines) < max_lines:
        lines.append(current)
    return lines or [(text or "Code")[:width]]


def _normalize_lang(language: str) -> str:
    lang = (language or "java").strip().lower()
    if lang in {"js", "node"}:
        return "javascript"
    return lang


def _preview_lines(language: str, source: str | None, max_lines: int = 10) -> list[str]:
    """Pick a complete-looking snippet. Empty source → no fake stub program."""
    raw = (source or "").replace("\t", "    ")
    if not raw.strip():
        return []
    rows = [line.rstrip() for line in raw.splitlines() if line.strip()]
    if not rows:
        return []
    return _complete_snippet(rows, max_lines=max_lines)


def _complete_snippet(rows: list[str], max_lines: int = 10) -> list[str]:
    if len(rows) <= max_lines:
        return _balance_display(rows)

    starts = [0]
    for index, line in enumerate(rows):
        low = line.lstrip().casefold()
        if any(
            token in low
            for token in (
                "void main",
                "public static",
                "def ",
                "function ",
                "const ",
                "let ",
                "for ",
                "while ",
                "class ",
                "async ",
            )
        ):
            starts.append(index)

    best = rows[:max_lines]
    best_score = -10_000
    for start in starts:
        window = rows[start : start + max_lines]
        if len(window) < 3 and start != 0:
            continue
        opens = sum(line.count("{") for line in window)
        closes = sum(line.count("}") for line in window)
        last = window[-1].strip()
        ends_complete = last in {"}", "};", "})", "main()", "run();"} or last.startswith("}")
        score = min(opens, closes) * 3 - abs(opens - closes) * 2
        score += 12 if ends_complete else 0
        score += sum(1 for line in window if len(line.strip()) > 10)
        # Prefer windows that include a body line (indent) not only signatures.
        score += sum(2 for line in window if line.startswith((" ", "\t")) and "{" not in line)
        if score > best_score:
            best_score = score
            best = window
    return _balance_display(best)


def _balance_display(rows: list[str]) -> list[str]:
    """Close open braces so the poster never looks like a chopped method."""
    depth = 0
    for line in rows:
        depth += line.count("{") - line.count("}")
    out = list(rows)
    while depth > 0 and len(out) < 14:
        indent = "    " * max(0, depth - 1)
        out.append(f"{indent}}}")
        depth -= 1
    return out


def _format_code_row(line: str, max_chars: int = 56) -> str:
    """Single display row for SVG thumbs (nbsp indent). Prefer soft wrap via _format_code_rows."""
    rows = _format_code_rows(line, max_chars=max_chars)
    return rows[0] if rows else ""


def _format_code_rows(line: str, max_chars: int = 56) -> list[str]:
    """Keep full statements visible: wrap long lines instead of cropping with …"""
    expanded = (line or "").replace("\t", "    ").rstrip()
    if not expanded:
        return [" "]
    leading = len(expanded) - len(expanded.lstrip(" "))
    indent = "\u00a0" * min(leading, 16)
    body = expanded.lstrip(" ")
    if len(body) <= max_chars:
        return [indent + body]
    rows: list[str] = []
    rest = body
    cont = indent + ("\u00a0" * 2)
    first = True
    while rest:
        width = max_chars if first else max(24, max_chars - 2)
        if len(rest) <= width:
            rows.append((indent if first else cont) + rest)
            break
        cut = width
        for sep in (" ", ",", "(", ")", ".", "{"):
            pos = rest.rfind(sep, 12, width)
            if pos >= 12:
                cut = pos + (0 if sep == " " else 1)
                break
        chunk = rest[:cut].rstrip()
        rows.append((indent if first else cont) + chunk)
        rest = rest[cut:].lstrip()
        first = False
        if len(rows) >= 3:
            if rest:
                rows[-1] = rows[-1][: max(8, max_chars - 1)] + "…"
            break
    return rows


def _heading_key(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").casefold()).strip()


def _distinct_subtitle(headline: str, topic: str) -> str:
    sub = strip_duration_copy(topic) or (topic or "").strip()
    head = _heading_key(headline)
    other = _heading_key(sub)
    if not other or other == head or other in head or head in other:
        return ""
    return sub[:56]



def _diagram_kind(topic: str, reel_mode: str | None = None) -> str:
    blob = f"{topic or ''} {reel_mode or ''}".lower()
    if re.search(r"hash\s*map|hashtable|hash\s*table", blob):
        return "hashmap"
    if re.search(r"garbage|garbege|\bgc\b|heap|mark\s*[- ]?\s*sweep|collector", blob):
        return "gc"
    if re.search(r"why\s*learn\s*python|learn\s*python|\bpython\b", blob) and re.search(
        r"why|learn|beginner|start|should|career|versatile", blob
    ):
        return "python_why"
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



def _catchy_hook(topic: str, spoken_language: str | None = None, seed: int = 0) -> tuple[str, str]:
    """Return (hook, subline) — Hindi hooks when spoken_language is hi (वाह!), else English clickbait."""
    lang = (spoken_language or "en").strip().lower()
    blob = (topic or "").lower()
    hindi = lang in {"hi", "hindi", "mr", "bn", "gu", "ta", "te", "kn", "pa"} or lang.startswith("hi")

    if hindi:
        hooks = [
            ("वाह!", "ये सीक्रेट सबको पता होना चाहिए"),
            ("रुको!", "90% लोग ये गलत समझते हैं"),
            ("कमाल!", "सिर्फ 60 सेकंड में क्लियर"),
            ("सच??", "इतना आसान था क्या?"),
            ("देखो!", "डायग्राम से दिमाग में बैठ जाएगा"),
        ]
        if re.search(r"hash\s*map|hashtable", blob):
            hooks = [
                ("वाह!", "HashMap अंदर से ऐसा दिखता है"),
                ("रुको!", "Collision पर क्या होता है?"),
                ("कमाल!", "O(1) का असली राज"),
            ]
        elif re.search(r"garbage|\bgc\b|heap", blob):
            hooks = [
                ("वाह!", "GC मेमोरी ऐसे साफ़ करता है"),
                ("रुको!", "Mark & Sweep आसान भाषा में"),
                ("कमाल!", "Heap में ज़िंदा vs मरा हुआ"),
            ]
    else:
        hooks = [
            ("WAIT!", "Most beginners get this wrong"),
            ("OMG", "This diagram makes it click"),
            ("STOP!", "Learn this in 60 seconds"),
            ("WOW", "The missing mental model"),
            ("HOOK", "Save this before you code"),
        ]
        if re.search(r"why\s*learn\s*python|learn\s*python|python\s*\?", blob) or (
            "python" in blob and re.search(r"why|should|beginner|start", blob)
        ):
            hooks = [
                ("WAIT!", "Python looks easy… until this"),
                ("WHY?", "1 language → AI, web, jobs"),
                ("OMG", "English-like code that ships"),
                ("STOP!", "The real reason pros pick Python"),
            ]
        if re.search(r"hash\s*map|hashtable", blob):
            hooks = [
                ("WAIT!", "HashMap internals in one glance"),
                ("WOW", "Collisions made visual"),
                ("STOP!", "Buckets + chaining demystified"),
            ]
        elif re.search(r"garbage|\bgc\b|heap", blob):
            hooks = [
                ("WAIT!", "See GC mark & sweep visually"),
                ("WOW", "Heap cleanup finally makes sense"),
                ("STOP!", "Live vs dead objects"),
            ]
    pick = hooks[seed % len(hooks)]
    return pick[0], pick[1]

def write_explainer_svg_poster(
    dest: Path,
    topic: str,
    title: str,
    language: str,
    reel_mode: str | None = None,
    spoken_language: str | None = None,
) -> Path:
    """Full-bleed 9:16 explainer poster with a large topic diagram (not a tiny footer card)."""
    mode = (reel_mode or "explainer").strip().lower() or "explainer"
    accent = "#22d3ee"
    glow = "#fbbf24"
    ink = "#ecfeff"
    headline = strip_duration_copy(title) or strip_duration_copy(topic) or topic or "Explainer"
    lines = _wrap(headline, 16, 3)
    seed = int(hashlib.sha256(f"{headline}|explainer|v15|{spoken_language or ''}".encode()).hexdigest()[:8], 16)
    kind = _diagram_kind(topic, mode)
    badge = "EXPLAINER" if mode != "info" else "INFO REEL"
    hook, subline = _catchy_hook(topic, spoken_language, seed)

    title_svg = []
    # Big clickbait hook first (वाह! / WAIT!)
    title_svg.append(
        f'<rect x="72" y="250" rx="22" width="{min(520, 48 + len(hook) * 42)}" height="78" fill="{glow}"/>'
        f'<text x="96" y="304" font-size="48" font-family="ui-sans-serif, system-ui, sans-serif" '
        f'font-weight="900" fill="#18181b">{html.escape(hook)}</text>'
    )
    title_svg.append(
        f'<text x="72" y="360" font-size="28" font-family="ui-sans-serif, system-ui, sans-serif" '
        f'font-weight="700" fill="{accent}">{html.escape(subline)}</text>'
    )
    y = 430
    for line in lines:
        title_svg.append(
            f'<text x="72" y="{y}" font-size="64" font-family="ui-sans-serif, system-ui, sans-serif" '
            f'font-weight="800" fill="{ink}">{html.escape(line)}</text>'
        )
        y += 78

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
  <text x="72" y="1820" font-size="24" font-family="ui-sans-serif, system-ui" letter-spacing="4" fill="#a1a1aa">TECHSHALA BY PAVI</text>
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
    if kind == "python_why":
        return _svg_python_why_v8(accent, glow, ink, topic, panel_w, panel_h)
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



def _svg_python_why_v8(accent: str, glow: str, ink: str, topic: str, panel_w: int, panel_h: int) -> str:
    """Viral metaphor: readable syntax → multi-domain apps → career demand."""
    parts = [
        f'<text x="36" y="48" font-size="22" font-family="ui-sans-serif, system-ui" font-weight="800" '
        f'letter-spacing="4" fill="{accent}">WHY PYTHON?</text>',
        f'<text x="36" y="88" font-size="28" font-family="ui-sans-serif, system-ui" font-weight="700" fill="{ink}">'
        f'Reads like English → ships everywhere</text>',
    ]
    cards = [
        ("1", "Syntax", "print(\"Hi\")", accent),
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

def write_svg_poster(
    dest: Path,
    topic: str,
    title: str,
    language: str,
    code: str | None = None,
    *,
    reel_mode: str | None = None,
    spoken_language: str | None = None,
) -> Path:
    mode = (reel_mode or "").strip().lower()
    if mode in {"explainer", "info"}:
        return write_explainer_svg_poster(dest, topic, title, language, reel_mode=mode, spoken_language=spoken_language)
    lang = _normalize_lang(language)
    colors = PALETTES.get(lang, PALETTES["java"])
    headline = strip_duration_copy(title) or strip_duration_copy(topic) or topic or "Coding short"
    lines = _wrap(headline, 18, 3)
    seed = int(hashlib.sha256(f"{headline}|{lang}".encode()).hexdigest()[:8], 16)
    title_svg = []
    y = 430
    for line in lines:
        title_svg.append(
            f'<text x="72" y="{y}" font-size="92" font-family="ui-sans-serif, system-ui, sans-serif" '
            f'font-weight="800" fill="{colors["ink"]}">{html.escape(line)}</text>'
        )
        y += 108
    subtitle = html.escape(_distinct_subtitle(headline, topic))
    if subtitle:
        title_svg.append(
            f'<text x="72" y="{y + 12}" font-size="36" font-family="ui-sans-serif, system-ui" '
            f'fill="#a1a1aa">{subtitle}</text>'
        )
        y += 56
    footer_top = 1700
    # Soft tilt; leave extra air under the headline so the raised corner never covers title text.
    tilt = -3.2 + ((seed % 9) - 4) * 0.1
    card_w_est = 936
    # Approx how far a rotated top corner lifts toward the title.
    tilt_lift = int(abs(math.sin(math.radians(tilt))) * (card_w_est * 0.55) + 36)
    code_top = min(max(y + 72 + tilt_lift, 720), 1120)
    row_h = 46
    max_rows = max(5, (footer_top - code_top - 120) // row_h)
    preview = _preview_lines(lang, code, max_lines=max_rows)
    use_diagram = (not preview) or mode in {"explainer", "info"}
    # Explainers prefer diagram even if stub code leaked in
    if mode in {"explainer", "info"}:
        preview = []
        use_diagram = True
    # Count wrapped display rows so the card is tall enough before drawing.
    if preview:
        display_rows = 0
        for row in preview:
            display_rows += len(_format_code_rows(row, max_chars=58))
        # Drop source lines until wrapped rows fit the available vertical band.
        while preview and (row_h * display_rows + 108) > (footer_top - code_top - 24):
            preview = preview[:-1]
            display_rows = sum(len(_format_code_rows(row, max_chars=58)) for row in preview)
        card_h = row_h * max(display_rows, 1) + 108
    else:
        card_h = 520 if use_diagram else 120
    if code_top + card_h > footer_top:
        card_h = max(140, footer_top - code_top)
    card_w = 936
    cx0 = 72 + card_w / 2
    cy0 = code_top + card_h / 2
    code_inner = []
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
        # Window chrome
        code_inner.append(
            '<circle cx="40" cy="28" r="8" fill="#fb7185"/><circle cx="68" cy="28" r="8" fill="#fbbf24"/>'
            '<circle cx="96" cy="28" r="8" fill="#34d399"/>'
            f'<text x="130" y="34" font-size="20" font-family="ui-sans-serif, system-ui" fill="#71717a">'
            f'{html.escape(lang)}.demo</text>'
        )
        cy = 78
        display_index = 0
        for index, row in enumerate(preview):
            fill = colors["accent"] if index == hero else "#e4e4e7"
            for formatted in _format_code_rows(row, max_chars=58):
                display_index += 1
                code_inner.append(
                    f'<text x="28" y="{cy}" font-size="18" font-family="{_MONO}" fill="#52525b">'
                    f"{display_index:02d}</text>"
                    f'<text x="78" y="{cy}" xml:space="preserve" font-size="23" font-family="{_MONO}" '
                    f'fill="{fill}">{html.escape(formatted)}</text>'
                )
                cy += row_h
        panel = (
            f'<rect x="0" y="0" rx="28" width="{card_w}" height="{card_h}" fill="#09090b" fill-opacity="0.92"/>'
            f'<rect x="0" y="0" width="14" height="{card_h}" rx="7" fill="{colors["accent"]}"/>'
            f'<rect x="0" y="0" rx="28" width="{card_w}" height="{card_h}" fill="none" '
            f'stroke="{colors["glow"]}" stroke-opacity="0.35" stroke-width="2"/>'
            + "".join(code_inner)
        )
    elif use_diagram:
        panel = (
            f'<rect x="0" y="0" rx="28" width="{card_w}" height="{card_h}" fill="#09090b" fill-opacity="0.88"/>'
            f'{_diagram_svg(topic, mode, colors["accent"], colors["glow"], colors["ink"], seed)}'
        )
    else:
        panel = (
            f'<rect x="0" y="0" rx="28" width="{card_w}" height="{card_h}" fill="#09090b" fill-opacity="0.88"/>'
            f'<text x="40" y="70" font-size="28" font-family="ui-sans-serif, system-ui" '
            f'fill="#a1a1aa">Explain reel · concept only</text>'
        )
    # Drop shadow + tilted card group
    code_block = (
        f'<g transform="translate({cx0:.1f}, {cy0:.1f}) rotate({tilt:.2f}) translate({-cx0:.1f}, {-cy0:.1f})">'
        f'<rect x="90" y="{code_top + 22}" rx="28" width="{card_w}" height="{card_h}" '
        f'fill="#000" fill-opacity="0.45"/>'
        f'<g transform="translate(72, {code_top})">{panel}</g>'
        f"</g>"
    )
    dest.write_text(
        f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 1920" width="1080" height="1920">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{colors["bg0"]}"/>
      <stop offset="100%" stop-color="{colors["bg1"]}"/>
    </linearGradient>
  </defs>
  <rect width="1080" height="1920" fill="url(#bg)"/>
  <circle cx="{900 + (seed % 40)}" cy="{160 + (seed % 50)}" r="{220 + (seed % 80)}" fill="{colors["glow"]}" fill-opacity="0.18"/>
  <circle cx="{120}" cy="{1680}" r="{280 + (seed % 60)}" fill="{colors["accent"]}" fill-opacity="0.12"/>
  <rect x="72" y="96" rx="28" width="360" height="72" fill="#fff"/>
  <text x="252" y="144" text-anchor="middle" font-size="28" font-family="ui-sans-serif, system-ui" font-weight="800" fill="#18181b">TECHSHALA</text>
  <text x="72" y="240" font-size="26" font-family="ui-sans-serif, system-ui" letter-spacing="8" fill="{colors["accent"]}">{html.escape((mode.upper() if mode in {"explainer", "info"} else lang.upper()))}</text>
  {code_block}
  {"".join(title_svg)}
  <text x="72" y="1760" font-size="30" font-family="ui-sans-serif, system-ui" fill="{colors["accent"]}">@{html.escape("techshalabypavi")}</text>
  <text x="72" y="1820" font-size="24" font-family="ui-sans-serif, system-ui" letter-spacing="4" fill="#a1a1aa">TECHSHALA BY PAVI</text>
</svg>
""",
        encoding="utf-8",
    )
    return dest


def ensure_reel_thumbnail(
    lesson_id: str,
    topic: str,
    title: str,
    language: str,
    code: str | None = None,
    *,
    reel_mode: str | None = None,
    spoken_language: str | None = None,
) -> str:
    folder = images_dir()
    svg_path = folder / f"thumb_{lesson_id}.svg"
    poster_title = strip_duration_copy(topic) or strip_duration_copy(title) or topic
    write_svg_poster(
        svg_path,
        topic,
        poster_title,
        language,
        code,
        reel_mode=reel_mode,
        spoken_language=spoken_language,
    )
    # Prefer PNG for dashboard/img tags — avoids stubborn SVG caching and sharper cards.
    png_path = svg_path.with_suffix(".png")
    try:
        import subprocess as _sp
        _sp.run(
            [
                "magick",
                "-background",
                "none",
                str(svg_path),
                "-resize",
                "540x960",
                str(png_path),
            ],
            check=True,
            capture_output=True,
        )
        digest = hashlib.sha256(png_path.read_bytes()).hexdigest()[:10]
        return f"/images/{png_path.name}?v={THUMB_VERSION}-{digest}"
    except Exception:
        digest = hashlib.sha256(svg_path.read_bytes()).hexdigest()[:10]
        return f"/images/{svg_path.name}?v={THUMB_VERSION}-{digest}"
