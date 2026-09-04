from __future__ import annotations

import html
import logging
from pathlib import Path

from app.config import settings
from app.services.images.base import get_image_provider
from app.services.locale import strip_duration_copy

logger = logging.getLogger(__name__)


def images_dir() -> Path:
    path = Path(settings.storage_path) / "images"
    path.mkdir(parents=True, exist_ok=True)
    return path


def thumbnail_prompt(topic: str, language: str) -> str:
    return (
        f"Vertical 9:16 cinematic social-media thumbnail for a coding reel. "
        f"Topic: {topic}. Language: {language}. "
        f"Dark glossy background, neon amber and cyan light, huge readable title '{topic}', "
        f"small badge 'BYTE', abstract code rain, no watermarks, no celebrity faces, "
        f"high contrast, catchy, viral educational poster."
    )


def write_svg_poster(dest: Path, topic: str, title: str, language: str) -> Path:
    safe_topic = html.escape(topic[:48] or "Coding short")
    safe_title = html.escape(title[:56] or safe_topic)
    safe_lang = html.escape(language.upper()[:16] or "CODE")
    dest.write_text(
        f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 1920" width="1080" height="1920">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#09090b"/>
      <stop offset="55%" stop-color="#1c1917"/>
      <stop offset="100%" stop-color="#0e7490"/>
    </linearGradient>
  </defs>
  <rect width="1080" height="1920" fill="url(#bg)"/>
  <circle cx="920" cy="180" r="260" fill="#fbbf24" fill-opacity="0.16"/>
  <circle cx="120" cy="1680" r="320" fill="#22d3ee" fill-opacity="0.12"/>
  <rect x="72" y="96" rx="28" width="280" height="72" fill="#fbbf24"/>
  <text x="212" y="144" text-anchor="middle" font-size="34" font-family="ui-sans-serif, system-ui" font-weight="800" fill="#18181b">BYTE</text>
  <text x="72" y="240" font-size="28" font-family="ui-sans-serif, system-ui" letter-spacing="8" fill="#fde68a">{safe_lang}</text>
  <text x="72" y="430" font-size="86" font-family="ui-sans-serif, system-ui" font-weight="800" fill="#fff7ed">{safe_title}</text>
  <text x="72" y="540" font-size="40" font-family="ui-sans-serif, system-ui" fill="#a1a1aa">{safe_topic}</text>
  <text x="72" y="1780" font-size="32" font-family="ui-sans-serif, system-ui" letter-spacing="6" fill="#fbbf24">BYTE · AI CODING TUTOR</text>
</svg>
""",
        encoding="utf-8",
    )
    return dest


def ensure_reel_thumbnail(lesson_id: str, topic: str, title: str, language: str) -> str:
    folder = images_dir()
    svg_path = folder / f"thumb_{lesson_id}.svg"
    png_path = folder / f"thumb_{lesson_id}.png"
    poster_title = strip_duration_copy(title) or topic
    write_svg_poster(svg_path, topic, poster_title, language)
    try:
        provider = get_image_provider()
        if provider.name != "local":
            provider.generate(
                thumbnail_prompt(topic, language),
                png_path,
                aspect_ratio="9:16",
                seed=abs(hash(lesson_id)) % 10_000,
                style="cinematic viral educational poster",
            )
            if png_path.exists() and png_path.stat().st_size > 800:
                return f"/images/{png_path.name}"
    except Exception:
        logger.warning("Gemini thumbnail failed for %s; using SVG poster", lesson_id, exc_info=True)
    return f"/images/{svg_path.name}"
