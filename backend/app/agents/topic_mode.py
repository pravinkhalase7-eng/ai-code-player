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
- Summary ({span(4, 6)}): One punchy takeaway. 2-3 short takeaways. Ask them to follow / save / comment.
- Spoken style: short sentences, catchy, not a lecture. No filler.
- Never say "{target} seconds" or "in this short" in narration or titles.
- spoken_language must match the tutor plan for all spoken lines, bullets, takeaways, and the title.
- lesson_id should be a short slug.
- language may stay as requested for metadata, but there is no program.
""".strip()
