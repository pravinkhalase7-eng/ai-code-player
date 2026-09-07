from pathlib import Path

path = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder/backend/app/services/images/thumbnail.py")
text = path.read_text()

old = '''    footer_top = 1700
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
'''

new = '''    footer_top = 1700
    # Soft tilt; leave extra air under the headline so the raised corner never covers title text.
    tilt = -4.2 + ((seed % 11) - 5) * 0.12
    card_w_est = 936
    # Approx how far a rotated top corner lifts toward the title.
    import math
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
    card_h = (row_h * max(len(preview), 1) + 108) if preview else (520 if use_diagram else 120)
    if code_top + card_h > footer_top:
        card_h = max(140, footer_top - code_top)
'''

if old not in text:
    raise SystemExit('position block not found')
text = text.replace(old, new, 1)

# Move title after code_block in the SVG so headline paints above the card
old_svg = '''  <text x="72" y="240" font-size="26" font-family="ui-sans-serif, system-ui" letter-spacing="8" fill="{colors["accent"]}">{html.escape((mode.upper() if mode in {"explainer", "info"} else lang.upper()))}</text>
  {"".join(title_svg)}
  {code_block}
'''
new_svg = '''  <text x="72" y="240" font-size="26" font-family="ui-sans-serif, system-ui" letter-spacing="8" fill="{colors["accent"]}">{html.escape((mode.upper() if mode in {"explainer", "info"} else lang.upper()))}</text>
  {code_block}
  {"".join(title_svg)}
'''
if old_svg not in text:
    raise SystemExit('svg order block not found')
text = text.replace(old_svg, new_svg, 1)

text = text.replace('THUMB_VERSION = "tilt-v11-code"', 'THUMB_VERSION = "tilt-v12-clear"', 1)

# math import at top of file if needed
if 'import math' not in text.split('def write_svg_poster')[0]:
    # we used inline import math inside function via the new block - that's fine (import math inside write_svg_poster)
    pass

path.write_text(text)
# Prefer module-level math import and remove inline
if 'import math\n' not in text[:400]:
    text = path.read_text()
    text = text.replace('from __future__ import annotations\n\n', 'from __future__ import annotations\n\nimport math\n', 1)
    text = text.replace('    import math\n    tilt_lift', '    tilt_lift')
    path.write_text(text)

import ast
ast.parse(path.read_text())
print('ok', 'tilt-v12-clear' in path.read_text())
