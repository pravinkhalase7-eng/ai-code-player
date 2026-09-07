from pathlib import Path

stage = Path("frontend/components/player/ReelStage.tsx")
text = stage.read_text()

text = text.replace(
    'import { boardKindLabel, isExplainMotionLesson, lessonExplainedTopics, synthesizeBoardSteps } from "@/lib/explainerVisuals";',
    'import { boardKindLabel, isExplainMotionLesson, lessonExplainedTopicDetails, lessonExplainedTopics, synthesizeBoardSteps } from "@/lib/explainerVisuals";',
    1,
)

old_memo = '''  const explainedTopics = useMemo(
    () => (explainMotion || isExplainMotionLesson(lesson) ? lessonExplainedTopics(lesson) : []),
    [explainMotion, lesson],
  );
  const summaryRecap = scene.type === "summary" && explainedTopics.length > 0;'''

new_memo = '''  const explainedTopics = useMemo(
    () => (explainMotion || isExplainMotionLesson(lesson) ? lessonExplainedTopics(lesson) : []),
    [explainMotion, lesson],
  );
  const explainedTopicDetails = useMemo(
    () => (explainMotion || isExplainMotionLesson(lesson) ? lessonExplainedTopicDetails(lesson) : []),
    [explainMotion, lesson],
  );
  const summaryRecap = scene.type === "summary" && explainedTopics.length > 0;'''

if old_memo not in text:
    raise SystemExit('memo block missing')
text = text.replace(old_memo, new_memo, 1)

old_list = '''                <div className="flex min-h-0 flex-1 flex-col gap-1.5">
                  {explainedTopics.map((item, index) => {
                    const visible = (infoAnim?.visibleCount ?? 0) > index;
                    const active = infoAnim?.active === index;
                    return (
                      <p
                        key={`recap-${index}-${item}`}
                        className={cn(
                          "info-bullet rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-[14px] font-semibold leading-5 text-zinc-100",
                          visible && "is-visible",
                          active && "is-active",
                        )}
                      >
                        <span className="mr-2 inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-cyan-400/25 px-1.5 text-[10px] font-bold text-cyan-50">
                          {visible ? "✓" : index + 1}
                        </span>
                        {item}
                      </p>
                    );
                  })}
                </div>'''

new_list = '''                <div className="flex min-h-0 flex-1 flex-col gap-1.5">
                  {explainedTopics.map((item, index) => {
                    const visible = (infoAnim?.visibleCount ?? 0) > index;
                    const active = infoAnim?.active === index;
                    const detail = explainedTopicDetails[index] || "";
                    return (
                      <div
                        key={`recap-${index}-${item}`}
                        className={cn(
                          "info-bullet flex items-start gap-3 rounded-xl border border-white/10 bg-black/40 px-3 py-2.5 text-zinc-100",
                          visible && "is-visible",
                          active && "is-active",
                        )}
                      >
                        <span
                          className={cn(
                            "mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[11px] font-bold",
                            visible
                              ? "bg-emerald-400/25 text-emerald-100"
                              : "bg-cyan-400/25 text-cyan-50",
                          )}
                          aria-hidden
                        >
                          {visible ? "✓" : index + 1}
                        </span>
                        <span className="min-w-0 flex-1">
                          <span className="block text-[14px] font-semibold leading-5 tracking-normal">
                            {item}
                          </span>
                          {detail ? (
                            <span className="mt-0.5 block text-[11px] font-medium leading-4 text-cyan-100/75">
                              {detail}
                            </span>
                          ) : null}
                        </span>
                      </div>
                    );
                  })}
                </div>'''

if old_list not in text:
    raise SystemExit('list block missing')
text = text.replace(old_list, new_list, 1)
stage.write_text(text)
print('ReelStage ok')

vis = Path("frontend/lib/explainerVisuals.ts")
v = vis.read_text()
if 'lessonExplainedTopicDetails' not in v:
    # append after lessonExplainedTopics
    idx = v.find('export function lessonExplainedTopics')
    start = v.find('{', idx)
    depth = 0
    end = start
    for i, ch in enumerate(v[start:], start):
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    helper = '''

/** One-line plain-English details aligned with lessonExplainedTopics titles. */
export function lessonExplainedTopicDetails(lesson: Lesson): string[] {
  const titles = lessonExplainedTopics(lesson);
  const scenes = lesson.scenes || [];
  const details: string[] = [];
  for (const scene of scenes) {
    if (scene.type !== "concept") continue;
    const steps = scene.diagram_steps || [];
    if (steps.length) {
      for (const step of steps) {
        details.push(String(step.detail || "").trim());
      }
      break;
    }
  }
  while (details.length < titles.length) details.push("");
  return details.slice(0, titles.length);
}
'''
    v = v[:end] + helper + v[end:]
    vis.write_text(v)
    print('helper ok')
else:
    print('helper exists')

exp = Path("frontend/lib/reelExport.ts")
e = exp.read_text()
old_x = 'ctx.fillText(line, x + pad + 42, by + 20 + li * 18);'
new_x = 'ctx.fillText(line, x + pad + 52, by + 20 + li * 18);'
if old_x in e:
    exp.write_text(e.replace(old_x, new_x, 1))
    print('export ok')
else:
    print('export x already ok or missing')
print('done')
