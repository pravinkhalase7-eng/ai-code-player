from pathlib import Path
import re

path = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder/backend/app/services/images/thumbnail.py")
text = path.read_text()

# bump version for cache bust
text2 = text
if 'THUMB_VERSION = "viral-v10-ctr"' in text2:
    text2 = text2.replace('THUMB_VERSION = "viral-v10-ctr"', 'THUMB_VERSION = "tilt-v11-code"', 1)
elif 'THUMB_VERSION =' in text2:
    text2 = re.sub(r'THUMB_VERSION = "[^"]+"', 'THUMB_VERSION = "tilt-v11-code"', text2, count=1)

old = '''    footer_top = 1700
    code_top = min(max(y + 56, 980), 1180)
    row_h = 44
    max_rows = max(4, (footer_top - code_top - 100) // row_h)
    preview = _preview_lines(lang, code, max_lines=max_rows)
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
'''

new = '''    footer_top = 1700
    # Sit the program card close under the headline (old min 980 left a big empty band).
    code_top = min(max(y + 40, 640), 1100)
    row_h = 46
    max_rows = max(5, (footer_top - code_top - 120) // row_h)
    preview = _preview_lines(lang, code, max_lines=max_rows)
    use_diagram = (not preview) or mode in {"explainer", "info"}
    # Explainers prefer diagram even if stub code leaked in
    if mode in {"explainer", "info"}:
        preview = []
        use_diagram = True
    card_h = (row_h * max(len(preview), 1) + 108) if preview else (520 if use_diagram else 120)
    if code_top + card_h > footer_top:
        card_h = max(140, footer_top - code_top)
    # Mild cinematic tilt — looks like a floating IDE card, not a flat slab.
    tilt = -6.5 + ((seed % 17) - 8) * 0.15
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
  {"".join(title_svg)}
  {code_block}
  <text x="72" y="1760" font-size="30" font-family="ui-sans-serif, system-ui" fill="{colors["accent"]}">@{html.escape("techshalabypavi")}</text>
  <text x="72" y="1820" font-size="24" font-family="ui-sans-serif, system-ui" letter-spacing="4" fill="#a1a1aa">AI CODING TUTOR</text>
  <rect x="{72 + drift}" y="1640" width="180" height="8" rx="4" fill="{colors["glow"]}" fill-opacity="0.7"/>
</svg>
""",
        encoding="utf-8",
    )
    return dest
'''

if old not in text2:
    raise SystemExit('write_svg_poster block not found')
path.write_text(text2.replace(old, new, 1))
print('patched', path)
# quick syntax check
import ast
ast.parse(path.read_text())
print('syntax ok', 'tilt-v11' in path.read_text())
