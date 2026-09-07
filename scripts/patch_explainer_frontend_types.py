#!/usr/bin/env python3
"""Frontend types, api, spokenLanguage for explainer."""
from pathlib import Path

ROOT = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder")

# spokenLanguage.ts
sp = ROOT / "frontend/lib/spokenLanguage.ts"
st = sp.read_text(encoding="utf-8")
st = st.replace(
    'export type MakeMode = "lesson" | "reel" | "info";',
    'export type MakeMode = "lesson" | "reel" | "info" | "explainer";',
    1,
)
st = st.replace(
    '    if (stored === "reel" || stored === "info") return stored;',
    '    if (stored === "reel" || stored === "info" || stored === "explainer") return stored;',
    1,
)
sp.write_text(st, encoding="utf-8")
print("spokenLanguage ok")

# api.ts
api = ROOT / "frontend/lib/api.ts"
at = api.read_text(encoding="utf-8")
old_create = '''export function createLesson(
  topic: string,
  language = "java",
  level = "beginner",
  format: "lesson" | "reel" = "lesson",
  spokenLanguage = "en",
  reelSeconds = 30,
  requiresCode?: boolean,
) {
  return request<{ lesson_id: string; status: string; job_id: string }>(
    "/api/v1/tutor/lesson",
    {
      method: "POST",
      body: JSON.stringify({
        topic,
        language,
        level,
        format,
        spoken_language: spokenLanguage,
        reel_seconds: format === "reel" ? reelSeconds : 30,
        ...(typeof requiresCode === "boolean" ? { requires_code: requiresCode } : {}),
      }),
    },
  );
}'''
new_create = '''export function createLesson(
  topic: string,
  language = "java",
  level = "beginner",
  format: "lesson" | "reel" = "lesson",
  spokenLanguage = "en",
  reelSeconds = 30,
  requiresCode?: boolean,
  reelMode?: string,
) {
  return request<{ lesson_id: string; status: string; job_id: string }>(
    "/api/v1/tutor/lesson",
    {
      method: "POST",
      body: JSON.stringify({
        topic,
        language,
        level,
        format,
        spoken_language: spokenLanguage,
        reel_seconds: format === "reel" ? reelSeconds : 30,
        ...(typeof requiresCode === "boolean" ? { requires_code: requiresCode } : {}),
        ...(reelMode ? { reel_mode: reelMode } : {}),
      }),
    },
  );
}'''
if old_create not in at:
    raise SystemExit("createLesson missing")
at = at.replace(old_create, new_create, 1)
api.write_text(at, encoding="utf-8")
print("api ok")

# types/lesson.ts
types = ROOT / "frontend/types/lesson.ts"
tt = types.read_text(encoding="utf-8")
if "diagram_steps" not in tt:
    tt = tt.replace(
        "  bullets?: string[];\n"
        "  takeaways?: string[];\n",
        "  bullets?: string[];\n"
        "  diagram_steps?: { title: string; detail?: string }[];\n"
        "  takeaways?: string[];\n",
        1,
    )
if "reel_mode" not in tt:
    tt = tt.replace(
        "  reel_seconds?: number;\n"
        "  requires_code?: boolean;\n"
        "};\n"
        "\n"
        "export type LessonSummary = {",
        "  reel_seconds?: number;\n"
        "  requires_code?: boolean;\n"
        "  reel_mode?: string | null;\n"
        "};\n"
        "\n"
        "export type LessonSummary = {",
        1,
    )
    tt = tt.replace(
        "  thumbnail_url?: string | null;\n"
        "  reel_seconds?: number;\n"
        "};",
        "  thumbnail_url?: string | null;\n"
        "  reel_seconds?: number;\n"
        "  reel_mode?: string | null;\n"
        "  requires_code?: boolean;\n"
        "};",
        1,
    )
types.write_text(tt, encoding="utf-8")
print("types ok")
print("done")
