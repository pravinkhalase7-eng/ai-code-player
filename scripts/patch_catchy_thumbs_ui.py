from pathlib import Path
import re
import json
import sqlite3
import hashlib
import subprocess
import sys

ROOT = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder")

# ---------- backend thumbnail hooks ----------
thumb = ROOT / "backend/app/services/images/thumbnail.py"
text = thumb.read_text()
text = text.replace('THUMB_VERSION = "diagram-v8-hero"', 'THUMB_VERSION = "diagram-v9-hook"')

if "def _catchy_hook" not in text:
    helpers = r'''
def _catchy_hook(topic: str, spoken_language: str | None = None, seed: int = 0) -> tuple[str, str]:
    """Return (hook, subline) — Hindi hooks when spoken_language is hi (वाह!), else English clickbait."""
    lang = (spoken_language or "en").strip().lower()
    blob = (topic or "").lower()
    hindi = lang in {"hi", "hindi", "mr", "bn", "gu", "ta", "te", "kn", "pa"} or lang.startswith("hi")

    if hindi:
        hooks = [
            ("वाह!", "ये सीक्रेट सबको पता होना चाहिए"),
            ("रुको!", "90% लोग ये गलत समझते हैं"),
            ("कमाल!", "सिर्फ 60 सेकंड में क्लियर"),
            ("सच??", "इतना आसान था क्या?"),
            ("देखो!", "डायग्राम से दिमाग में बैठ जाएगा"),
        ]
        if re.search(r"hash\s*map|hashtable", blob):
            hooks = [
                ("वाह!", "HashMap अंदर से ऐसा दिखता है"),
                ("रुको!", "Collision पर क्या होता है?"),
                ("कमाल!", "O(1) का असली राज"),
            ]
        elif re.search(r"garbage|\bgc\b|heap", blob):
            hooks = [
                ("वाह!", "GC मेमोरी ऐसे साफ़ करता है"),
                ("रुको!", "Mark & Sweep आसान भाषा में"),
                ("कमाल!", "Heap में ज़िंदा vs मरा हुआ"),
            ]
    else:
        hooks = [
            ("WAIT!", "Most beginners get this wrong"),
            ("OMG", "This diagram makes it click"),
            ("STOP!", "Learn this in 60 seconds"),
            ("WOW", "The missing mental model"),
            ("HOOK", "Save this before you code"),
        ]
        if re.search(r"hash\s*map|hashtable", blob):
            hooks = [
                ("WAIT!", "HashMap internals in one glance"),
                ("WOW", "Collisions made visual"),
                ("STOP!", "Buckets + chaining demystified"),
            ]
        elif re.search(r"garbage|\bgc\b|heap", blob):
            hooks = [
                ("WAIT!", "See GC mark & sweep visually"),
                ("WOW", "Heap cleanup finally makes sense"),
                ("STOP!", "Live vs dead objects"),
            ]
    pick = hooks[seed % len(hooks)]
    return pick[0], pick[1]

'''
    # insert before write_explainer
    marker = "def write_explainer_svg_poster("
    if marker not in text:
        raise SystemExit("write_explainer missing")
    text = text.replace(marker, helpers + marker, 1)

# Update write_explainer signature + hook rendering
old_expl = '''def write_explainer_svg_poster(
    dest: Path,
    topic: str,
    title: str,
    language: str,
    reel_mode: str | None = None,
) -> Path:
    """Full-bleed 9:16 explainer poster with a large topic diagram (not a tiny footer card)."""
    mode = (reel_mode or "explainer").strip().lower() or "explainer"
    accent = "#22d3ee"
    glow = "#fbbf24"
    ink = "#ecfeff"
    headline = strip_duration_copy(title) or strip_duration_copy(topic) or topic or "Explainer"
    lines = _wrap(headline, 16, 3)
    seed = int(hashlib.sha256(f"{headline}|explainer|v8".encode()).hexdigest()[:8], 16)
    kind = _diagram_kind(topic, mode)
    badge = "EXPLAINER" if mode != "info" else "INFO REEL"

    title_svg = []
    y = 280
    for line in lines:
        title_svg.append(
            f'<text x="72" y="{y}" font-size="78" font-family="ui-sans-serif, system-ui, sans-serif" '
            f'font-weight="800" fill="{ink}">{html.escape(line)}</text>'
        )
        y += 92
'''

new_expl = '''def write_explainer_svg_poster(
    dest: Path,
    topic: str,
    title: str,
    language: str,
    reel_mode: str | None = None,
    spoken_language: str | None = None,
) -> Path:
    """Full-bleed 9:16 explainer poster with a large topic diagram (not a tiny footer card)."""
    mode = (reel_mode or "explainer").strip().lower() or "explainer"
    accent = "#22d3ee"
    glow = "#fbbf24"
    ink = "#ecfeff"
    headline = strip_duration_copy(title) or strip_duration_copy(topic) or topic or "Explainer"
    lines = _wrap(headline, 16, 3)
    seed = int(hashlib.sha256(f"{headline}|explainer|v9|{spoken_language or ''}".encode()).hexdigest()[:8], 16)
    kind = _diagram_kind(topic, mode)
    badge = "EXPLAINER" if mode != "info" else "INFO REEL"
    hook, subline = _catchy_hook(topic, spoken_language, seed)

    title_svg = []
    # Big clickbait hook first (वाह! / WAIT!)
    title_svg.append(
        f'<rect x="72" y="250" rx="22" width="{min(520, 48 + len(hook) * 42)}" height="78" fill="{glow}"/>'
        f'<text x="96" y="304" font-size="48" font-family="ui-sans-serif, system-ui, sans-serif" '
        f'font-weight="900" fill="#18181b">{html.escape(hook)}</text>'
    )
    title_svg.append(
        f'<text x="72" y="360" font-size="28" font-family="ui-sans-serif, system-ui, sans-serif" '
        f'font-weight="700" fill="{accent}">{html.escape(subline)}</text>'
    )
    y = 430
    for line in lines:
        title_svg.append(
            f'<text x="72" y="{y}" font-size="64" font-family="ui-sans-serif, system-ui, sans-serif" '
            f'font-weight="800" fill="{ink}">{html.escape(line)}</text>'
        )
        y += 78
'''
if old_expl not in text:
    raise SystemExit("write_explainer head not found")
text = text.replace(old_expl, new_expl, 1)

# panel_top uses y - already does min(max(y+40...

# Update call from write_svg_poster
text = text.replace(
    "return write_explainer_svg_poster(dest, topic, title, language, reel_mode=mode)",
    "return write_explainer_svg_poster(dest, topic, title, language, reel_mode=mode, spoken_language=spoken_language)",
)

# write_svg_poster needs spoken_language param
old_ws = '''def write_svg_poster(
    dest: Path,
    topic: str,
    title: str,
    language: str,
    code: str | None = None,
    *,
    reel_mode: str | None = None,
) -> Path:
    mode = (reel_mode or "").strip().lower()
    if mode in {"explainer", "info"}:
        return write_explainer_svg_poster(dest, topic, title, language, reel_mode=mode, spoken_language=spoken_language)
'''
new_ws = '''def write_svg_poster(
    dest: Path,
    topic: str,
    title: str,
    language: str,
    code: str | None = None,
    *,
    reel_mode: str | None = None,
    spoken_language: str | None = None,
) -> Path:
    mode = (reel_mode or "").strip().lower()
    if mode in {"explainer", "info"}:
        return write_explainer_svg_poster(dest, topic, title, language, reel_mode=mode, spoken_language=spoken_language)
'''
if old_ws not in text:
    # try without spoken already in return
    old_ws2 = '''def write_svg_poster(
    dest: Path,
    topic: str,
    title: str,
    language: str,
    code: str | None = None,
    *,
    reel_mode: str | None = None,
) -> Path:
    mode = (reel_mode or "").strip().lower()
    if mode in {"explainer", "info"}:
        return write_explainer_svg_poster(dest, topic, title, language, reel_mode=mode)
'''
    if old_ws2 in text:
        text = text.replace(old_ws2, new_ws, 1)
    else:
        raise SystemExit("write_svg_poster sig not found")
else:
    text = text.replace(old_ws, new_ws, 1)

# ensure_reel_thumbnail
old_ens = '''def ensure_reel_thumbnail(
    lesson_id: str,
    topic: str,
    title: str,
    language: str,
    code: str | None = None,
    *,
    reel_mode: str | None = None,
) -> str:
    folder = images_dir()
    svg_path = folder / f"thumb_{lesson_id}.svg"
    poster_title = strip_duration_copy(topic) or strip_duration_copy(title) or topic
    write_svg_poster(
        svg_path, topic, poster_title, language, code, reel_mode=reel_mode
    )
'''
new_ens = '''def ensure_reel_thumbnail(
    lesson_id: str,
    topic: str,
    title: str,
    language: str,
    code: str | None = None,
    *,
    reel_mode: str | None = None,
    spoken_language: str | None = None,
) -> str:
    folder = images_dir()
    svg_path = folder / f"thumb_{lesson_id}.svg"
    poster_title = strip_duration_copy(topic) or strip_duration_copy(title) or topic
    write_svg_poster(
        svg_path,
        topic,
        poster_title,
        language,
        code,
        reel_mode=reel_mode,
        spoken_language=spoken_language,
    )
'''
if old_ens not in text:
    raise SystemExit("ensure sig not found")
text = text.replace(old_ens, new_ens, 1)
thumb.write_text(text)
print("thumbnail.py hooks ok")

# lesson_service pass spoken_language
svc = ROOT / "backend/app/services/lesson_service.py"
sv = svc.read_text()
sv = sv.replace(
    '''    url = ensure_reel_thumbnail(
        lesson.lesson_id,
        lesson.topic,
        lesson.topic,
        lesson.language,
        program,
        reel_mode=getattr(lesson, "reel_mode", None),
    )
''',
    '''    url = ensure_reel_thumbnail(
        lesson.lesson_id,
        lesson.topic,
        lesson.topic,
        lesson.language,
        program,
        reel_mode=getattr(lesson, "reel_mode", None),
        spoken_language=getattr(lesson, "spoken_language", None),
    )
''',
)
sv = sv.replace(
    '''                    "thumbnail_url": ensure_reel_thumbnail(
                        lesson.lesson_id,
                        lesson.topic,
                        lesson.topic,
                        lesson.language,
                        extract_primary_code(lesson.model_dump(mode="json"))[1],
                        reel_mode=getattr(lesson, "reel_mode", None),
                    )
''',
    '''                    "thumbnail_url": ensure_reel_thumbnail(
                        lesson.lesson_id,
                        lesson.topic,
                        lesson.topic,
                        lesson.language,
                        extract_primary_code(lesson.model_dump(mode="json"))[1],
                        reel_mode=getattr(lesson, "reel_mode", None),
                        spoken_language=getattr(lesson, "spoken_language", None),
                    )
''',
)
svc.write_text(sv)
print("lesson_service spoken_language passed")

# ---------- Dashboard UI ----------
dash = ROOT / "frontend/components/dashboard/Dashboard.tsx"
dt = dash.read_text()

# imports
if "generateThumbnail" not in dt:
    dt = dt.replace(
        'import { createLesson, deleteAllLessons, deleteLesson, getHealth, listLessons } from "@/lib/api";',
        'import { createLesson, deleteAllLessons, deleteLesson, generateThumbnail, getHealth, listLessons } from "@/lib/api";',
    )
if "ImageIcon" not in dt:
    dt = dt.replace(
        'import { ArrowRight, Clapperboard, GitBranch, Info, Sparkles, Timer, Trash2 } from "lucide-react";',
        'import { ArrowRight, Clapperboard, Expand, GitBranch, ImageIcon, Info, RefreshCw, Sparkles, Timer, Trash2, X } from "lucide-react";',
    )

# state
if "previewThumb" not in dt:
    dt = dt.replace(
        "  const [clearingAll, setClearingAll] = useState(false);\n",
        "  const [clearingAll, setClearingAll] = useState(false);\n"
        "  const [thumbBusyId, setThumbBusyId] = useState(\"\");\n"
        "  const [previewThumb, setPreviewThumb] = useState<{ url: string; title: string } | null>(null);\n",
    )

# functions after clearAllLessons
if "regenThumbnail" not in dt:
    insert_after = '''  async function clearAllLessons() {
    if (lessons.length === 0 || clearingAll) return;
    if (
      !window.confirm(
        `Delete all ${lessons.length} lesson${lessons.length === 1 ? "" : "s"}? This cannot be undone.`,
      )
    ) {
      return;
    }
    setClearingAll(true);
    setError("");
    try {
      await deleteAllLessons();
      setLessons([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not clear lessons");
    } finally {
      setClearingAll(false);
    }
  }
'''
    extra = '''  async function clearAllLessons() {
    if (lessons.length === 0 || clearingAll) return;
    if (
      !window.confirm(
        `Delete all ${lessons.length} lesson${lessons.length === 1 ? "" : "s"}? This cannot be undone.`,
      )
    ) {
      return;
    }
    setClearingAll(true);
    setError("");
    try {
      await deleteAllLessons();
      setLessons([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not clear lessons");
    } finally {
      setClearingAll(false);
    }
  }

  async function regenThumbnail(lesson: LessonSummary, event: MouseEvent) {
    event.stopPropagation();
    event.preventDefault();
    if (thumbBusyId) return;
    setThumbBusyId(lesson.lesson_id);
    setError("");
    try {
      const payload = await generateThumbnail(lesson.lesson_id, true);
      const url = payload.lesson.thumbnail_url || "";
      setLessons((current) =>
        current.map((item) =>
          item.lesson_id === lesson.lesson_id ? { ...item, thumbnail_url: url } : item,
        ),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not regenerate thumbnail");
    } finally {
      setThumbBusyId("");
    }
  }

  function openThumbPreview(lesson: LessonSummary, event: MouseEvent) {
    event.stopPropagation();
    event.preventDefault();
    const url = lesson.thumbnail_url || "";
    if (!url) return;
    setPreviewThumb({
      url,
      title: lesson.format === "reel" ? lesson.topic : lesson.title,
    });
  }
'''
    if insert_after not in dt:
        raise SystemExit("clearAllLessons block not found")
    dt = dt.replace(insert_after, extra, 1)

# Replace thumbnail area in card
old_thumb = '''                      {lesson.format === "reel" && lesson.thumbnail_url ? (
                        <div className="relative h-28 w-full overflow-hidden bg-zinc-900 sm:h-32">
                          <img src={lesson.thumbnail_url} alt="" className="h-full w-full object-cover" />
                          <span className="absolute left-3 top-3 rounded-full bg-amber-400 px-2 py-0.5 text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-950">
                            {lesson.reel_seconds ? `${lesson.reel_seconds}s` : "Short"}
                          </span>
                        </div>
                      ) : null}
'''
new_thumb = '''                      {lesson.format === "reel" && lesson.thumbnail_url ? (
                        <div className="relative h-36 w-full overflow-hidden bg-zinc-900 sm:h-44">
                          <img src={lesson.thumbnail_url} alt="" className="h-full w-full object-cover" />
                          <span className="absolute left-3 top-3 rounded-full bg-amber-400 px-2 py-0.5 text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-950">
                            {lesson.reel_seconds ? `${lesson.reel_seconds}s` : "Short"}
                          </span>
                          <div className="absolute bottom-2 right-2 z-10 flex gap-1.5">
                            <button
                              type="button"
                              title="View thumbnail fullscreen"
                              aria-label="View thumbnail fullscreen"
                              className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-white/20 bg-zinc-950/75 text-white backdrop-blur hover:border-cyan-300/50 hover:bg-cyan-500/20"
                              onClick={(event) => openThumbPreview(lesson, event)}
                            >
                              <Expand className="h-4 w-4" />
                            </button>
                            <button
                              type="button"
                              title="Regenerate thumbnail"
                              aria-label="Regenerate thumbnail"
                              disabled={thumbBusyId === lesson.lesson_id}
                              className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-white/20 bg-zinc-950/75 text-white backdrop-blur hover:border-amber-300/50 hover:bg-amber-500/20 disabled:opacity-50"
                              onClick={(event) => void regenThumbnail(lesson, event)}
                            >
                              <RefreshCw className={`h-4 w-4 ${thumbBusyId === lesson.lesson_id ? "animate-spin" : ""}`} />
                            </button>
                          </div>
                        </div>
                      ) : lesson.format === "reel" ? (
                        <div className="relative flex h-28 w-full items-center justify-center gap-2 bg-zinc-900/80 sm:h-32">
                          <button
                            type="button"
                            className="inline-flex items-center gap-1.5 rounded-full border border-amber-300/40 bg-amber-400/15 px-3 py-1.5 text-xs font-semibold text-amber-100"
                            disabled={thumbBusyId === lesson.lesson_id}
                            onClick={(event) => void regenThumbnail(lesson, event)}
                          >
                            <ImageIcon className="h-3.5 w-3.5" />
                            {thumbBusyId === lesson.lesson_id ? "Making…" : "Make thumbnail"}
                          </button>
                        </div>
                      ) : null}
'''
if old_thumb not in dt:
    raise SystemExit("dashboard thumb block not found")
dt = dt.replace(old_thumb, new_thumb, 1)

# Add lightbox before closing of root div - find end of component
if "previewThumb ?" not in dt:
    # before final closing of return
    old_end = '''      </section>
    </div>
  );
}
'''
    new_end = '''      </section>

      {previewThumb ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 p-4 backdrop-blur-sm"
          role="dialog"
          aria-modal="true"
          aria-label="Thumbnail preview"
          onClick={() => setPreviewThumb(null)}
        >
          <button
            type="button"
            className="absolute right-4 top-4 inline-flex h-11 w-11 items-center justify-center rounded-full border border-white/20 bg-zinc-950/80 text-white"
            aria-label="Close preview"
            onClick={() => setPreviewThumb(null)}
          >
            <X className="h-5 w-5" />
          </button>
          <div
            className="relative max-h-[92vh] w-full max-w-md overflow-hidden rounded-2xl border border-white/15 bg-zinc-950 shadow-2xl"
            onClick={(event) => event.stopPropagation()}
          >
            <img src={previewThumb.url} alt={previewThumb.title} className="h-auto w-full object-contain" />
            <p className="border-t border-white/10 px-4 py-3 text-sm font-semibold text-zinc-100">{previewThumb.title}</p>
          </div>
        </div>
      ) : null}
    </div>
  );
}
'''
    if old_end not in dt:
        raise SystemExit("dashboard end not found")
    dt = dt.replace(old_end, new_end, 1)

dash.write_text(dt)
print("Dashboard UI ok")

# Also add fullscreen on LessonPlayer thumbnail button area - quick: after makeThumbnail exists, add preview
# Skip heavy LessonPlayer for now - dashboard is main ask. Player already has Thumbnail button.

# Regen all lessons
sys.path.insert(0, str(ROOT / "backend"))
import os
os.chdir(ROOT / "backend")
from importlib import reload
import app.services.images.thumbnail as th
reload(th)

con = sqlite3.connect(ROOT / "backend/tutor.db")
images = Path(th.images_dir())
alt = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/storage/images")
alt.mkdir(parents=True, exist_ok=True)
for lid, raw in con.execute("select id, lesson_json from lessons"):
    p = json.loads(raw)
    if p.get("format") != "reel":
        continue
    url = th.ensure_reel_thumbnail(
        p.get("lesson_id") or lid,
        p.get("topic") or "",
        p.get("topic") or "",
        p.get("language") or "java",
        None,
        reel_mode=p.get("reel_mode"),
        spoken_language=p.get("spoken_language"),
    )
    p["thumbnail_url"] = url
    p["thumbnail_custom"] = False
    con.execute("update lessons set lesson_json=? where id=?", (json.dumps(p, ensure_ascii=False), lid))
    svg = images / f"thumb_{lid}.svg"
    body = svg.read_text(encoding="utf-8") if svg.exists() else ""
    print(lid[:24], url)
    print("  hooks", [m for m in ["वाह!", "रुको!", "WAIT!", "WOW", "कमाल!", "Roots", "INTERNALS"] if m in body])
    for ext in [".svg", ".png"]:
        f = images / f"thumb_{lid}{ext}"
        if f.exists():
            import shutil
            shutil.copy2(f, alt / f.name)
con.commit()
con.close()
print("THUMB", th.THUMB_VERSION)
