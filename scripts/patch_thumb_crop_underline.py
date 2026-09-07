from pathlib import Path
import re

path = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder/backend/app/services/images/thumbnail.py")
text = path.read_text()

# 1) Smarter code row formatting: wrap instead of harsh ellipsis crop
old_fmt = '''def _format_code_row(line: str, max_chars: int = 48) -> str:
    expanded = (line or "").replace("\\t", "    ").rstrip()
    leading = len(expanded) - len(expanded.lstrip(" "))
    body = expanded.lstrip(" ")
    # Keep indent readable; prefer wrapping feel via ellipsis only on very long lines.
    if len(body) > max_chars:
        body = body[: max_chars - 1] + "…"
    return ("\\u00a0" * min(leading, 20)) + body
'''

new_fmt = '''def _format_code_row(line: str, max_chars: int = 56) -> str:
    """Single display row for SVG thumbs (nbsp indent). Prefer soft wrap via _format_code_rows."""
    rows = _format_code_rows(line, max_chars=max_chars)
    return rows[0] if rows else ""


def _format_code_rows(line: str, max_chars: int = 56) -> list[str]:
    """Keep full statements visible: wrap long lines instead of cropping with …"""
    expanded = (line or "").replace("\\t", "    ").rstrip()
    if not expanded:
        return [" "]
    leading = len(expanded) - len(expanded.lstrip(" "))
    indent = "\\u00a0" * min(leading, 16)
    body = expanded.lstrip(" ")
    if len(body) <= max_chars:
        return [indent + body]
    rows: list[str] = []
    rest = body
    cont = indent + ("\\u00a0" * 2)
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
'''

if old_fmt not in text:
    raise SystemExit('format_code_row block missing')
text = text.replace(old_fmt, new_fmt, 1)

# 2) In write_svg_poster: milder tilt, fit height to lines, wrap rows, remove underline, bump version
# Replace the preview rendering loop and related geometry

old_loop = '''    if preview:
        # Window chrome
        code_inner.append(
            '<circle cx="40" cy="28" r="8" fill="#fb7185"/><circle cx="68" cy="28" r="8" fill="#fbbf24"/>'
            '<circle cx="96" cy="28" r="8" fill="#34d399"/>'
            f'<text x="130" y="34" font-size="22" font-family="ui-sans-serif, system-ui" fill="#71717a">'
            f'{html.escape(lang)}.demo</text>'
        )
        cy = 78
        for index, row in enumerate(preview):
            fill = colors["accent"] if index == hero else "#e4e4e7"
            formatted = _format_code_row(row)
            code_inner.append(
                f'<text x="36" y="{cy}" font-size="20" font-family="{_MONO}" fill="#52525b">'
                f"{index + 1:02d}</text>"
                f'<text x="88" y="{cy}" xml:space="preserve" font-size="26" font-family="{_MONO}" '
                f'fill="{fill}">{html.escape(formatted)}</text>'
            )
            cy += row_h
'''

new_loop = '''    if preview:
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
        # Grow card to fit wrapped lines (avoid bottom crop).
        needed_h = cy + 28
        if needed_h > card_h:
            card_h = min(footer_top - code_top - 24, max(card_h, needed_h))
            cy0 = code_top + card_h / 2
'''

if old_loop not in text:
    raise SystemExit('preview loop missing')
text = text.replace(old_loop, new_loop, 1)

# Softer tilt + slightly earlier code_top already set; reduce tilt further
text = text.replace(
    'tilt = -4.2 + ((seed % 11) - 5) * 0.12',
    'tilt = -3.2 + ((seed % 9) - 4) * 0.1',
    1,
)

# Wider usable card: keep 936 but ok
# Remove decorative underline bar
old_bar = '''  <text x="72" y="1760" font-size="30" font-family="ui-sans-serif, system-ui" fill="{colors["accent"]}">@{html.escape("techshalabypavi")}</text>
  <text x="72" y="1820" font-size="24" font-family="ui-sans-serif, system-ui" letter-spacing="4" fill="#a1a1aa">AI CODING TUTOR</text>
  <rect x="{72 + drift}" y="1640" width="180" height="8" rx="4" fill="{colors["glow"]}" fill-opacity="0.7"/>
</svg>
'''
new_bar = '''  <text x="72" y="1760" font-size="30" font-family="ui-sans-serif, system-ui" fill="{colors["accent"]}">@{html.escape("techshalabypavi")}</text>
  <text x="72" y="1820" font-size="24" font-family="ui-sans-serif, system-ui" letter-spacing="4" fill="#a1a1aa">AI CODING TUTOR</text>
</svg>
'''
if old_bar not in text:
    raise SystemExit('underline bar block missing')
text = text.replace(old_bar, new_bar, 1)

# drift may become unused - check if drift used elsewhere in write_svg_poster
# if only for bar, leave variable (harmless) or remove
text = text.replace('THUMB_VERSION = "tilt-v12-clear"', 'THUMB_VERSION = "tilt-v13-fullcode"', 1)

path.write_text(text)
import ast
ast.parse(path.read_text())
print('patched ok')
# drift unused warning - fine
if 'drift' in path.read_text() and '72 + drift' not in path.read_text():
    # remove unused drift line in write_svg_poster to keep clean
    text = path.read_text()
    text = text.replace('    drift = 80 + (seed % 140)\n', '', 1)
    path.write_text(text)
    ast.parse(path.read_text())
    print('removed unused drift')
