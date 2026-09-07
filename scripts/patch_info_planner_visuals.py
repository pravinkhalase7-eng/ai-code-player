#!/usr/bin/env python3
from pathlib import Path
ROOT = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder")
tm = ROOT / "backend/app/agents/topic_mode.py"
tt = tm.read_text(encoding="utf-8")
# Only patch the INFO planner (explain_reel_planner_instruction), not explainer which already has rules.
# Find the info planner block uniquely.
old = '''Hard rules:
- Intro ({span(6, 8)}): Hook in the first sentence. Name the idea with a question or common misconception. Never open with stop scrolling.
- Concept ({span(14, 18)}): Teach the idea clearly in spoken sentences. Include 4-6 short bullets that a viewer can read on screen.
- Summary ({span(4, 6)}): One punchy takeaway. 2-3 short takeaways. Ask them to follow / save / comment.
- Spoken style: short sentences, catchy, not a lecture. No filler.
'''
new = '''Hard rules:
- Intro ({span(6, 8)}): Hook in the first sentence. Name the idea with a question or common misconception. Never open with stop scrolling.
- Concept ({span(14, 18)}): Teach the idea clearly in spoken sentences. Include 4-6 short bullets that a viewer can read on screen.
- EVERY scene MUST fill visual: {{"kind": "...", "title": "...", "callouts": [...], "particles": true}}.
  Never leave visual.kind as "none" or callouts empty.
  - intro.visual.kind = "hook"; callouts = 2-3 short cold-open phrases.
  - concept.visual.kind = "bullets"; callouts = the on-screen bullets.
  - summary.visual.kind = "takeaway"; callouts = the takeaways list.
- Summary ({span(4, 6)}): One punchy takeaway. 2-3 short takeaways. Ask them to follow / save / comment.
- Spoken style: short sentences, catchy, not a lecture. No filler.
'''
if old not in tt:
    if 'intro.visual.kind = "hook"; callouts = 2-3 short cold-open phrases.' in tt and "concept.visual.kind = \"bullets\"" in tt:
        print("info planner already patched")
    else:
        raise SystemExit("info planner block missing")
else:
    tt = tt.replace(old, new, 1)
    tm.write_text(tt, encoding="utf-8")
    print("info planner visual rules ok")
