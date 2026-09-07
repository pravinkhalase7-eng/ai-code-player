from pathlib import Path
import re

ROOT = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder")

NEW_PROMPT_FN = r'''
def thumbnail_prompt(
    topic: str,
    language: str,
    *,
    spoken_language: str | None = None,
    reel_mode: str | None = None,
) -> str:
    """High-CTR viral Shorts poster prompt (Gemini / image providers)."""
    topic_clean = strip_duration_copy(topic) or topic or "Coding"
    lang = _normalize_lang(language)
    mode = (reel_mode or "").strip().lower()
    spoken = (spoken_language or "en").strip().lower()
    hindi = spoken in {"hi", "hindi"} or spoken.startswith("hi")

    # Derive a short shouty headline + curiosity hook from the topic.
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

    # Topic-specific floating cards (collections example style).
    blob = topic_clean.lower()
    if re.search(r"collection|arraylist|hashset|hashmap|queue|list\b|set\b|map\b", blob):
        cards = "ArrayList, HashSet, HashMap, Queue"
        visual = (
            "glowing Java logo in the upper-middle; surround it with large colorful floating "
            "data-structure cards labeled ArrayList, HashSet, HashMap, Queue; glowing data flowing "
            "between the structures (speed, complexity, organization)"
        )
    elif re.search(r"hash\s*map|hashtable", blob):
        cards = "Buckets, hash(), index, Node.next"
        visual = (
            "glowing HashMap whiteboard: vertical buckets, chained nodes, hash→index motion; "
            "neon put/collision energy"
        )
    elif re.search(r"garbage|\bgc\b|heap", blob):
        cards = "Allocate, Mark, Sweep, Compact"
        visual = (
            "glowing GC heap with live vs dead objects, mark & sweep energy beams, "
            "futuristic memory cleanup scene"
        )
    else:
        cards = "Idea, Break it, Trace, Result"
        visual = (
            f"futuristic {lang} programming scene with a glowing language emblem upper-middle; "
            f"large neon concept cards ({cards}); light trails connecting them"
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

'''

thumb = ROOT / "backend/app/services/images/thumbnail.py"
text = thumb.read_text()
# Replace old thumbnail_prompt function
pattern = re.compile(
    r"def thumbnail_prompt\(topic: str, language: str\) -> str:.*?return \(\n(?:.*?\n)*?.*?\)\n",
    re.S,
)
m = pattern.search(text)
if not m:
    # try simpler find
    start = text.find("def thumbnail_prompt(")
    if start < 0:
        raise SystemExit("thumbnail_prompt not found")
    # find next def at same indent
    end = text.find("\ndef ", start + 1)
    if end < 0:
        raise SystemExit("end not found")
    text = text[:start] + NEW_PROMPT_FN.lstrip("\n") + text[end:]
else:
    text = pattern.sub(NEW_PROMPT_FN.lstrip("\n"), text, count=1)

# bump version note in ensure if present
text = text.replace('THUMB_VERSION = "diagram-v9-hook"', 'THUMB_VERSION = "viral-v10-ctr"')
thumb.write_text(text)
print("backend thumbnail_prompt updated")

# frontend thumbnailPrompt.ts
fe = ROOT / "frontend/lib/thumbnailPrompt.ts"
fe.write_text(
    '''import type { Lesson } from "@/types/lesson";

/**
 * High-CTR viral Shorts poster prompt (matches backend thumbnail_prompt).
 * Used when copying a Gemini-style prompt from the player.
 */
export function buildThumbnailPrompt(lesson: Lesson, seed = 42): string {
  const topic = (lesson.topic || lesson.title || "Coding short").trim();
  const language = (lesson.language || "java").trim();
  const spoken = (lesson.spoken_language || "en").trim().toLowerCase();
  const mode = (lesson.reel_mode || "").trim().toLowerCase();
  const hindi = spoken === "hi" || spoken.startsWith("hi") || spoken === "hindi";

  const words = topic.match(/[A-Za-z0-9+#]+/g) || [];
  let headline = words.slice(0, 4).map((w) => w.toUpperCase()).join(" ") || language.toUpperCase();
  if (headline.length > 28) headline = `${headline.slice(0, 28).trimEnd()}…`;

  const hooks = hindi
    ? ["कौन सा?", "वाह!", "रुको!", "ये कैसे?", "सच??"]
    : ["WHICH ONE?", "WAIT…", "MOST MISS THIS", "THIS OR THAT?", "WHY?"];
  const hook = hooks[Math.abs(seed) % hooks.length];

  const blob = topic.toLowerCase();
  let visual: string;
  if (/collection|arraylist|hashset|hashmap|queue|\\blist\\b|\\bset\\b|\\bmap\\b/.test(blob)) {
    visual =
      "glowing Java logo upper-middle; large floating cards ArrayList, HashSet, HashMap, Queue; glowing data flowing between them";
  } else if (/hash\\s*map|hashtable/.test(blob)) {
    visual =
      "glowing HashMap whiteboard: buckets, chained nodes, hash→index motion, neon collision energy";
  } else if (/garbage|\\bgc\\b|heap/.test(blob)) {
    visual =
      "glowing GC heap with live vs dead objects, mark & sweep beams, futuristic memory cleanup";
  } else {
    visual = `futuristic ${language} scene with glowing emblem upper-middle; neon concept cards; light trails`;
  }

  const explain = mode === "explainer" || mode === "info" ? "how-it-works explainer" : "coding short";

  return (
    `Create a highly catchy, high-CTR vertical 9:16 thumbnail/poster for a programming video. ` +
    `Topic: ${topic}. Language: ${language}. Format: ${explain}. ` +
    `Main headline in huge bold typography: "${headline}". ` +
    `Curiosity hook in a smaller highly contrasting text box: "${hook}". ` +
    `Visual: ${visual}. ` +
    `Composition: logo/main visual upper-middle; headline near center huge bold; curiosity hook in contrasting box; ` +
    `keep text off extreme edges; mobile-clear; strong vertical flow; clean uncluttered. ` +
    `Colors: dark black/navy with Java red, orange, electric blue, purple neon; glow, depth, shadows. ` +
    `Style: viral coding thumbnail, premium YouTube Shorts, futuristic, cinematic lighting, bold 3D type, ` +
    `neon glow, high contrast, sharp, dynamic, professional, striking. ` +
    `Communicate "${topic} made simple" instantly while creating curiosity. ` +
    `Aspect 9:16, 1080×1920, mobile-first. No watermark, no clutter. seed ${seed}.`
  );
}
'''
)
print("frontend thumbnailPrompt updated")

# Sanity import
import sys
sys.path.insert(0, str(ROOT / "backend"))
from app.services.images.thumbnail import thumbnail_prompt, THUMB_VERSION
print(THUMB_VERSION)
print(thumbnail_prompt("Java Collections", "java", spoken_language="en", reel_mode="explainer")[:280])
print("---")
print(thumbnail_prompt("how hashmap works", "java", spoken_language="hi", reel_mode="explainer")[:280])
