from __future__ import annotations

import re

from app.schemas.lesson import normalize_reel_seconds


def topic_requires_code(topic: str) -> bool:
    """False for conceptual topics that cannot be a small runnable program."""
    text = (topic or "").strip()
    blob = text.casefold()

    # Strong concept signals first (AI / systems literacy).
    concept_patterns = (
        r"\brag\b",
        r"\bagentic\b",
        r"retrieval[-\s]?augmented",
        r"large language model",
        r"\bllms?\b",
        r"\bchatgpt\b",
        r"\bgpt-?\d*\b",
        r"\btransformer(s)?\b",
        r"neural network",
        r"machine learning",
        r"deep learning",
        r"artificial intelligence",
        r"\bprompt engineering\b",
        r"\btokenizer\b",
        r"attention mechanism",
        r"foundation model",
        r"generative ai",
        r"\bagi\b",
        r"diffusion model",
        r"\bembeddings?\b",
        r"vector (db|database|store|search)",
        r"\bhallucinat",
        r"\bretrieval\b",
        r"\bre-?ranking\b",
        r"\btool[-\s]?calling\b",
        r"\bmulti[-\s]?agent\b",
        r"\bagents?\b.*\b(rag|llm|ai)\b",
        r"\b(llm|ai|rag)\b.*\bagents?\b",
    )
    if any(re.search(pat, blob) for pat in concept_patterns):
        return False

    coding_hints = (
        "for loop", "while loop", "if else", "switch case",
        "variable", "function", "class ", "array", "string",
        "python", "java", "javascript", "typescript",
        "compile", "runtime", "debug", "regex",
        "sql select", "html", "css", "react", "algorithm",
        "recursion", "pointer", "thread", "async await", "promise",
        "callback", "hashmap", "linked list", "binary tree",
        "stream api", "lambda", "decorator", "closure",
    )
    has_coding = any(h in blob for h in coding_hints)
    if re.match(r"^(what is|what's|whats|explain|define)\b", blob) and not has_coding:
        return False
    if re.search(r"\b(concept|overview|introduction|explained)\b", blob) and not has_coding:
        return False
    return True



def explain_reel_planner_instruction(seconds: int = 30) -> str:
    target = normalize_reel_seconds(seconds)
    words_lo = int(round(target * 2.3))
    words_hi = int(round(target * 3.0))
    scale = target / 30.0

    def span(low: float, high: float) -> str:
        return f"{int(round(low * scale))}-{int(round(high * scale))}s"

    return f"""
You are the Lesson Planner Agent for an explain-only coding-literacy reel (no program).
The topic cannot be demonstrated with a tiny runnable program (examples: what is Agentic RAG, what is an LLM).
Create a hooky visual short. Total spoken time across ALL scenes MUST be about {target} seconds ({words_lo}-{words_hi} words total).
Set reel_seconds to {target}. Set requires_code to false. format must be "reel".

Required scenes IN THIS ORDER: intro, concept, summary.
Do NOT include code, execution, terminal, or quiz scenes.
Do NOT invent fake code, Main.java, for-loops, print statements, or sandbox output.

Hard rules:
- Intro ({span(6, 8)}): Hook in the first sentence. Name the idea with a question or common misconception. Never open with stop scrolling.
- Concept ({span(14, 18)}): Teach the idea clearly in spoken sentences. Include 4-6 short bullets that a viewer can read on screen.
- EVERY scene MUST fill visual: {{"kind": "...", "title": "...", "callouts": [...], "particles": true}}.
  Never leave visual.kind as "none" or callouts empty.
  - intro.visual.kind = "hook"; callouts = 2-3 short cold-open phrases.
  - concept.visual.kind = "bullets"; callouts = the on-screen bullets.
  - summary.visual.kind = "takeaway"; callouts = the takeaways list.
- Summary ({span(4, 6)}): One punchy takeaway. 2-3 short takeaways. Ask them to follow / save / comment.
- Spoken style: short sentences, catchy, not a lecture. No filler.
- Never say "{target} seconds" or "in this short" in narration or titles.
- spoken_language must match the tutor plan for all spoken lines, bullets, takeaways, and the title.
- lesson_id should be a short slug.
- language may stay as requested for metadata, but there is no program.
""".strip()


def topic_is_hashmap(topic: str) -> bool:
    blob = (topic or "").casefold()
    return bool(
        re.search(r"hash\s*map|hashtable|hash\s*table|map\s+internals|internal.*map", blob)
    )


def default_hashmap_visual() -> dict:
    """Phone-friendly HashMap board demo (capacity 8, one collision)."""
    return {
        "kind": "hashmap",
        "capacity": 8,
        "init_code": "Map<String,Integer> map = new HashMap<>();",
        "setup_lines": [],
        "puts": [
            {
                "code": 'map.put("Mia",95)',
                "key": "Mia",
                "value": "95",
                "hash_bits": "1010",
                "bucket": 2,
                "color": "orange",
            },
            {
                "code": 'map.put("Leo",88)',
                "key": "Leo",
                "value": "88",
                "hash_bits": "0101",
                "bucket": 5,
                "color": "blue",
            },
            {
                "code": 'map.put("Zoe",92)',
                "key": "Zoe",
                "value": "92",
                "hash_bits": "1010",
                "bucket": 2,
                "color": "green",
            },
        ],
        "node_fields": ["key", "value", "hash", "next"],
    }


def explainer_reel_planner_instruction(seconds: int = 30) -> str:
    target = normalize_reel_seconds(seconds)
    words_lo = int(round(target * 2.3))
    words_hi = int(round(target * 3.0))
    scale = target / 30.0

    def span(low: float, high: float) -> str:
        return f"{int(round(low * scale))}-{int(round(high * scale))}s"

    return f"""
You are the Lesson Planner Agent for an EXPLAINER reel — a mechanism diagram short (no program).
The viewer wants to understand HOW something works internally (example: how HashMap works in Java).
Create a hooky visual short. Total spoken time across ALL scenes MUST be about {target} seconds ({words_lo}-{words_hi} words total).
Set reel_seconds to {target}. Set requires_code to false. Set reel_mode to "explainer". format must be "reel".

Required scenes IN THIS ORDER: intro, concept, summary.
Do NOT include code, execution, terminal, or quiz scenes.
Do NOT invent full runnable programs, Main.java classes, for-loop demos, print/sandbox output, or API-usage tutorials.
Tiny 1-line micro-examples ON diagram_steps.example are REQUIRED (see below) — those are not "fake code programs".
Do NOT teach how to call an API — teach the internal mechanism stages.

Hard rules:
- Intro ({span(6, 8)}): Hook with a misconception (e.g. "HashMap is just magic O(1)"). Never open with stop scrolling.
- Concept ({span(14, 18)}): Narrate HOW it works. MUST include 4-6 diagram_steps — each is a MECHANISM stage.
  Example for HashMap: empty buckets → node structure → put1 → put2 → collision put → takeaway.
  Also fill bullets with the diagram_steps titles (for older UI).
  Each diagram_step MUST be {{"title": "...", "detail": "...", "example": "..."}}.
  - title: max ~6 words; detail: one short clause.
  - example: REQUIRED — a tiny concrete snippet OR everyday analogy the viewer can relate to (1 line, under ~60 chars).
    Coding topics: micro code fragment only, e.g. `new Student()`, `obj = null`, `map.put("a",1)` hash path.
    NOT a full Main.java program, NOT a for-loop demo lesson, NOT multi-line runnable scenes.
  Short examples ON the diagram are allowed; full runnable program scenes are still forbidden.
- HASHMAP / hashtable / map-internals topics: MUST also fill concept.visual_diagram with kind "hashmap":
  - capacity: prefer 8 (phone-readable), not 16
  - init_code: e.g. Map<String,Integer> map = new HashMap<>();
  - setup_lines: optional short lines; prefer short string keys (Mia/Leo/Zoe) OR short labels (e1/Dev)
  - puts: 3–4 concrete put steps with colors (orange|blue|green), hash_bits, bucket indices
  - MUST include at least one collision (two puts same bucket) so next-chain is visible
  - node_fields: ["key","value","hash","next"]
  Concept narration should walk the puts. For non-hashmap explainer topics, visual_diagram may be null.
- EVERY scene MUST fill visual: {{"kind": "...", "title": "...", "callouts": [...], "particles": true}}.
  Never leave visual.kind as "none" or callouts empty.
  - intro.visual.kind = "hook"; callouts = 2-3 short cold-open phrases (misconception → twist).
  - concept.visual.kind = "board"; callouts = diagram_steps titles (same order).
  - summary.visual.kind = "takeaway"; callouts = the takeaways list.
- Summary ({span(4, 6)}): One punchy takeaway about the mechanism. 2-3 short takeaways. Ask them to follow / save / comment.
- Spoken style: short sentences, catchy, not a lecture. No filler.
- Never say "{target} seconds" or "in this short" in narration or titles.
- spoken_language must match the tutor plan for all spoken lines, bullets, diagram_steps (title/detail; keep code tokens in example), takeaways, and the title.
- lesson_id should be a short slug.
- language may stay as requested for metadata, but there is no program.
""".strip()

