#!/usr/bin/env python3
"""ReelStage diagram UI, CSS, LessonPlayer isExplain, reelExport."""
from pathlib import Path

ROOT = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder")

# ---- globals.css ----
css = ROOT / "frontend/app/globals.css"
ct = css.read_text(encoding="utf-8")
if ".explainer-node" not in ct:
    ct += """

.explainer-node {
  opacity: 0;
  transform: translateY(16px) scale(0.96);
  filter: blur(4px);
  transition: opacity 0.35s ease, transform 0.35s ease, filter 0.35s ease, border-color 0.25s ease, background 0.25s ease, box-shadow 0.25s ease;
}

.explainer-node.is-visible {
  opacity: 1;
  transform: translateY(0) scale(1);
  filter: blur(0);
}

.explainer-node.is-active {
  border-color: rgba(103, 232, 249, 0.6) !important;
  background: rgba(8, 51, 68, 0.72) !important;
  box-shadow: 0 0 0 1px rgba(34, 211, 238, 0.3), 0 10px 30px rgba(8, 145, 178, 0.35);
  animation: info-bullet-pop 0.45s cubic-bezier(0.22, 1, 0.36, 1);
}

.explainer-connector {
  height: 14px;
  width: 2px;
  margin: 0 auto;
  background: linear-gradient(180deg, rgba(34, 211, 238, 0.15), rgba(251, 191, 36, 0.55), rgba(34, 211, 238, 0.15));
  opacity: 0;
  transition: opacity 0.3s ease;
}

.explainer-connector.is-visible {
  opacity: 1;
}
"""
    css.write_text(ct, encoding="utf-8")
    print("globals.css ok")
else:
    print("globals.css already has explainer")

# ---- LessonPlayer isExplainLesson ----
lp = ROOT / "frontend/components/player/LessonPlayer.tsx"
lpt = lp.read_text(encoding="utf-8")
old_is = '''function isExplainLesson(lesson: Lesson): boolean {
  // Explicit Code short must never be treated as Info reel.
  if (lesson.requires_code === true) return false;
  if (lesson.requires_code === false) return true;'''
new_is = '''function isExplainLesson(lesson: Lesson): boolean {
  // Explicit Code short must never be treated as Info reel.
  if (lesson.requires_code === true && lesson.reel_mode !== "explainer" && lesson.reel_mode !== "info") return false;
  if (lesson.reel_mode === "explainer" || lesson.reel_mode === "info") return true;
  if (lesson.requires_code === false) return true;'''
if old_is not in lpt:
    raise SystemExit("isExplainLesson missing")
lpt = lpt.replace(old_is, new_is, 1)
# Also update subtitle chip if present
lpt = lpt.replace(
    '? lesson.requires_code === false ? `${spokenLabel} · Explain · ${lesson.topic}` : `${spokenLabel} · ${lesson.language} · ${lesson.topic}`',
    '? lesson.reel_mode === "explainer"\n'
    "                ? `${spokenLabel} · Explainer · ${lesson.topic}`\n"
    "                : lesson.requires_code === false\n"
    "                  ? `${spokenLabel} · Explain · ${lesson.topic}`\n"
    "                  : `${spokenLabel} · ${lesson.language} · ${lesson.topic}`",
    1,
)
lp.write_text(lpt, encoding="utf-8")
print("LessonPlayer ok")

# ---- ReelStage.tsx ----
rs = ROOT / "frontend/components/player/ReelStage.tsx"
rt = rs.read_text(encoding="utf-8")

# Replace concept detection + anim + rendering
old_concept_block = '''  const isConcept = scene.type === "concept" || ((scene.type === "code" || scene.type === "execution") && (!(code || "").trim() || lesson.requires_code === false));
  const infoAnim = useMemo(
    () => (isConcept ? infoBulletAt(scene.bullets || [], currentTime, duration) : null),
    [isConcept, scene.bullets, currentTime, duration],
  );'''

new_concept_block = '''  const isExplainer =
    lesson.reel_mode === "explainer" || Boolean(scene.diagram_steps && scene.diagram_steps.length);
  const isConcept =
    scene.type === "concept" ||
    ((scene.type === "code" || scene.type === "execution") &&
      (!(code || "").trim() || lesson.requires_code === false));
  const diagramSteps = useMemo(() => {
    const steps = (scene.diagram_steps || [])
      .map((s) => ({ title: String(s.title || "").trim(), detail: String(s.detail || "").trim() }))
      .filter((s) => s.title);
    if (steps.length) return steps;
    return (scene.bullets || []).map((b) => ({ title: String(b || "").trim(), detail: "" })).filter((s) => s.title);
  }, [scene.diagram_steps, scene.bullets]);
  const stepTitles = useMemo(() => diagramSteps.map((s) => s.title), [diagramSteps]);
  const infoAnim = useMemo(
    () => (isConcept ? infoBulletAt(isExplainer ? stepTitles : scene.bullets || [], currentTime, duration) : null),
    [isConcept, isExplainer, stepTitles, scene.bullets, currentTime, duration],
  );'''

if old_concept_block not in rt:
    raise SystemExit("concept block missing")
rt = rt.replace(old_concept_block, new_concept_block, 1)

old_ui = '''      ) : isConcept ? (
        <>
          <div className="pointer-events-none absolute inset-0 z-[2] overflow-hidden">
            <div className="info-orb bg-violet-500/45" style={{ width: 190, height: 190, left: -48, top: 110 }} />
            <div
              className="info-orb bg-fuchsia-400/30"
              style={{ width: 150, height: 150, right: -28, top: 260, animationDelay: "1.2s" }}
            />
            <div
              className="info-orb bg-cyan-400/25"
              style={{ width: 120, height: 120, left: 36, bottom: 250, animationDelay: "2.4s" }}
            />
          </div>
          <header className="relative z-10 shrink-0 px-1 pt-2 text-center">
            <p className="info-step-chip inline-flex rounded-full border border-violet-200/30 bg-violet-300/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-violet-100">
              Explain
            </p>
            <h2 className="mt-2 line-clamp-2 text-xl font-semibold leading-6 tracking-tight text-white">{topic}</h2>
          </header>
          <div className="relative z-10 flex min-h-0 flex-1 flex-col items-stretch justify-center py-2">
            <div className="flex max-h-full min-h-0 flex-col gap-2 overflow-y-auto rounded-2xl border border-violet-200/20 bg-[#12071f]/92 p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]">
              {(scene.bullets || []).length ? (
                (scene.bullets || []).map((item, index) => {
                  const visible = (infoAnim?.visibleCount ?? 0) > index;
                  const active = infoAnim?.active === index;
                  return (
                    <p
                      key={`${index}-${item}`}
                      className={cn(
                        "info-bullet rounded-xl border border-white/10 bg-black/35 px-3 py-2 text-sm font-medium leading-5 text-zinc-100",
                        visible && "is-visible",
                        active && "is-active",
                      )}
                    >
                      <span className="mr-2 inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-violet-400/25 px-1.5 text-[10px] font-bold text-violet-100">
                        {index + 1}
                      </span>
                      {item}
                    </p>
                  );
                })
              ) : (
                <p className="text-sm leading-6 text-zinc-200">{narration}</p>
              )}
            </div>
          </div>
        </>
      ) : ('''

new_ui = '''      ) : isConcept ? (
        <>
          <div className="pointer-events-none absolute inset-0 z-[2] overflow-hidden">
            <div
              className={cn("info-orb", isExplainer ? "bg-cyan-500/45" : "bg-violet-500/45")}
              style={{ width: 190, height: 190, left: -48, top: 110 }}
            />
            <div
              className={cn("info-orb", isExplainer ? "bg-amber-400/30" : "bg-fuchsia-400/30")}
              style={{ width: 150, height: 150, right: -28, top: 260, animationDelay: "1.2s" }}
            />
            <div
              className={cn("info-orb", isExplainer ? "bg-teal-400/25" : "bg-cyan-400/25")}
              style={{ width: 120, height: 120, left: 36, bottom: 250, animationDelay: "2.4s" }}
            />
          </div>
          <header className="relative z-10 shrink-0 px-1 pt-2 text-center">
            <p
              className={cn(
                "info-step-chip inline-flex rounded-full border px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em]",
                isExplainer
                  ? "border-cyan-200/30 bg-cyan-300/10 text-cyan-100"
                  : "border-violet-200/30 bg-violet-300/10 text-violet-100",
              )}
            >
              {isExplainer ? "Explainer" : "Explain"}
            </p>
            <h2 className="mt-2 line-clamp-2 text-xl font-semibold leading-6 tracking-tight text-white">{topic}</h2>
          </header>
          <div className="relative z-10 flex min-h-0 flex-1 flex-col items-stretch justify-center py-2">
            <div
              className={cn(
                "flex max-h-full min-h-0 flex-col gap-2 overflow-y-auto rounded-2xl border p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]",
                isExplainer
                  ? "border-cyan-200/20 bg-[#04151c]/92"
                  : "border-violet-200/20 bg-[#12071f]/92",
              )}
            >
              {isExplainer && diagramSteps.length ? (
                diagramSteps.map((item, index) => {
                  const visible = (infoAnim?.visibleCount ?? 0) > index;
                  const active = infoAnim?.active === index;
                  return (
                    <div key={`${index}-${item.title}`}>
                      {index > 0 ? (
                        <div className={cn("explainer-connector", visible && "is-visible")} />
                      ) : null}
                      <div
                        className={cn(
                          "explainer-node rounded-xl border border-white/10 bg-black/35 px-3 py-2",
                          visible && "is-visible",
                          active && "is-active",
                        )}
                      >
                        <p className="flex items-start gap-2 text-sm font-semibold leading-5 text-zinc-50">
                          <span className="mt-0.5 inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-cyan-400/25 px-1.5 text-[10px] font-bold text-cyan-100">
                            {index + 1}
                          </span>
                          <span className="min-w-0 flex-1">
                            {item.title}
                            {item.detail ? (
                              <span className="mt-0.5 block text-xs font-medium leading-4 text-cyan-100/75">
                                {item.detail}
                              </span>
                            ) : null}
                          </span>
                        </p>
                      </div>
                    </div>
                  );
                })
              ) : (scene.bullets || []).length ? (
                (scene.bullets || []).map((item, index) => {
                  const visible = (infoAnim?.visibleCount ?? 0) > index;
                  const active = infoAnim?.active === index;
                  return (
                    <p
                      key={`${index}-${item}`}
                      className={cn(
                        "info-bullet rounded-xl border border-white/10 bg-black/35 px-3 py-2 text-sm font-medium leading-5 text-zinc-100",
                        visible && "is-visible",
                        active && "is-active",
                      )}
                    >
                      <span className="mr-2 inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-violet-400/25 px-1.5 text-[10px] font-bold text-violet-100">
                        {index + 1}
                      </span>
                      {item}
                    </p>
                  );
                })
              ) : (
                <p className="text-sm leading-6 text-zinc-200">{narration}</p>
              )}
            </div>
          </div>
        </>
      ) : ('''

if old_ui not in rt:
    raise SystemExit("ReelStage UI block missing")
rt = rt.replace(old_ui, new_ui, 1)
rs.write_text(rt, encoding="utf-8")
print("ReelStage ok")
print("player patches done")
