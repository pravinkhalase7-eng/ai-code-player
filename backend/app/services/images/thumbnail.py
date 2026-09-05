from __future__ import annotations

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
THUMB_VERSION = "title-v4-en"


def images_dir() -> Path:
    path = Path(settings.storage_path) / "images"
    path.mkdir(parents=True, exist_ok=True)
    return path


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


def _preview_lines(language: str, source: str | None) -> list[str]:
    fallback = CODE_LINES.get(language, CODE_LINES["java"])
    raw = (source or "").replace("\t", "    ")
    if not raw.strip():
        return fallback
    rows: list[str] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        rows.append(line.rstrip())
        if len(rows) >= 8:
            break
    return rows or fallback


def _format_code_row(line: str, max_chars: int = 36) -> str:
    expanded = (line or "").replace("\t", "    ").rstrip()
    leading = len(expanded) - len(expanded.lstrip(" "))
    body = expanded.lstrip(" ")
    if len(body) > max_chars:
        body = body[: max_chars - 1] + "…"
    return ("\u00a0" * min(leading, 16)) + body


def _heading_key(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").casefold()).strip()


def _distinct_subtitle(headline: str, topic: str) -> str:
    sub = strip_duration_copy(topic) or (topic or "").strip()
    head = _heading_key(headline)
    other = _heading_key(sub)
    if not other or other == head or other in head or head in other:
        return ""
    return sub[:56]


def write_svg_poster(
    dest: Path,
    topic: str,
    title: str,
    language: str,
    code: str | None = None,
) -> Path:
    lang = _normalize_lang(language)
    colors = PALETTES.get(lang, PALETTES["java"])
    headline = strip_duration_copy(title) or strip_duration_copy(topic) or topic or "Coding short"
    lines = _wrap(headline, 18, 3)
    seed = int(hashlib.sha256(f"{headline}|{lang}".encode()).hexdigest()[:8], 16)
    drift = 80 + (seed % 140)
    preview = _preview_lines(lang, code)
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
    code_top = min(max(y + 72, 1040), 1280)
    row_h = 48
    card_h = row_h * len(preview) + 88
    code_svg = []
    cy = code_top + 64
    for index, row in enumerate(preview):
        fill = colors["accent"] if index in {0, 1} else "#d4d4d8"
        formatted = _format_code_row(row)
        code_svg.append(
            f'<text x="108" y="{cy}" font-size="22" font-family="{_MONO}" fill="#52525b">'
            f"{index + 1:02d}</text>"
            f'<text x="168" y="{cy}" xml:space="preserve" font-size="26" font-family="{_MONO}" '
            f'fill="{fill}">{html.escape(formatted)}</text>'
        )
        cy += row_h
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
  <text x="72" y="240" font-size="26" font-family="ui-sans-serif, system-ui" letter-spacing="8" fill="{colors["accent"]}">{html.escape(lang.upper())}</text>
  {"".join(title_svg)}
  <rect x="72" y="{code_top}" rx="28" width="936" height="{card_h}" fill="#09090b" fill-opacity="0.72"/>
  <rect x="72" y="{code_top}" width="12" height="{card_h}" rx="6" fill="{colors["accent"]}"/>
  {"".join(code_svg)}
  <text x="72" y="1760" font-size="30" font-family="ui-sans-serif, system-ui" fill="{colors["accent"]}">@{html.escape("techshalabypavi")}</text>
  <text x="72" y="1820" font-size="24" font-family="ui-sans-serif, system-ui" letter-spacing="4" fill="#a1a1aa">AI CODING TUTOR</text>
  <rect x="{72 + drift}" y="1640" width="180" height="8" rx="4" fill="{colors["glow"]}" fill-opacity="0.7"/>
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
) -> str:
    folder = images_dir()
    svg_path = folder / f"thumb_{lesson_id}.svg"
    poster_title = strip_duration_copy(topic) or strip_duration_copy(title) or topic
    write_svg_poster(svg_path, topic, poster_title, language, code)
    return f"/images/{svg_path.name}?v={THUMB_VERSION}"
