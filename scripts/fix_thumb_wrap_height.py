from pathlib import Path
import ast

path = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder/backend/app/services/images/thumbnail.py")
text = path.read_text()

old = '''    card_h = (row_h * max(len(preview), 1) + 108) if preview else (520 if use_diagram else 120)
    if code_top + card_h > footer_top:
        card_h = max(140, footer_top - code_top)
    card_w = 936
    cx0 = 72 + card_w / 2
    cy0 = code_top + card_h / 2
    code_inner = []
'''

new = '''    # Count wrapped display rows so the card is tall enough before drawing.
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
'''

if old not in text:
    raise SystemExit('card_h block missing')
text = text.replace(old, new, 1)

# Remove the late grow that can fight the transform / leave empty space inconsistently
old_grow = '''                cy += row_h
        # Grow card to fit wrapped lines (avoid bottom crop).
        needed_h = cy + 28
        if needed_h > card_h:
            card_h = min(footer_top - code_top - 24, max(card_h, needed_h))
            cy0 = code_top + card_h / 2
        panel = (
'''
new_grow = '''                cy += row_h
        panel = (
'''
if old_grow not in text:
    raise SystemExit('late grow block missing')
text = text.replace(old_grow, new_grow, 1)

path.write_text(text)
ast.parse(text)
print('height fix ok')
