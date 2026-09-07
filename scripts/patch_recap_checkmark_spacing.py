from pathlib import Path
import ast

# --- ReelStage: clearer checklist rows ---
stage = Path("frontend/components/player/ReelStage.tsx")
text = stage.read_text()

old = '''                <div className="flex min-h-0 flex-1 flex-col gap-1.5">
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

new = '''                <div className="flex min-h-0 flex-1 flex-col gap-1.5">
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

if old not in text:
    raise SystemExit('ReelStage recap block missing')
text = text.replace(old, new, 1)

# Add explainedTopicDetails next to explainedTopics useMemo
old_topics = '''  const explainedTopics = useMemo(
    () => lessonExplainedTopics(lesson),
    [lesson],
  );'''

# Check current form
if 'explainedTopics = useMemo' not in text:
    raise SystemExit('explainedTopics useMemo missing')

# Replace import and add helper usage for details
if 'lessonExplainedTopicDetails' not in text:
    text = text.replace(
        'lessonExplainedTopics',
        'lessonExplainedTopics,\n  lessonExplainedTopicDetails',
        1,
    )
    # fix if import line got messy - check
    # Find the useMemo block more flexibly
    import re
    m = re.search(
        r'const explainedTopics = useMemo\(\s*\(\)\s*=>\s*lessonExplainedTopics\(lesson\),\s*\[lesson\],\s*\);',
        text,
    )
    if not m:
        raise SystemExit('explainedTopics block pattern missing')
    replacement = '''const explainedTopics = useMemo(
    () => lessonExplainedTopics(lesson),
    [lesson],
  );
  const explainedTopicDetails = useMemo(
    () => lessonExplainedTopicDetails(lesson),
    [lesson],
  );'''
    text = text[:m.start()] + replacement + text[m.end():]

stage.write_text(text)
print('ReelStage patched')

# --- explainerVisuals: add details helper ---
vis = Path("frontend/lib/explainerVisuals.ts")
v = vis.read_text()
if 'lessonExplainedTopicDetails' not in v:
    # Find lessonExplainedTopics function and add sibling after it
    marker = 'export function lessonExplainedTopics'
    if marker not in v:
        raise SystemExit('lessonExplainedTopics missing')
    # Append after the function - read end of function
    idx = v.find(marker)
    # find next export or end
    rest = v[idx:]
    # Insert new function after lessonExplainedTopics body
    # Find closing of that function by brace count
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

/** Matching one-line details for recap rows (plain English under each title). */
export function lessonExplainedTopicDetails(lesson: Lesson): string[] {
  const scenes = lesson.scenes || [];
  const out: string[] = [];
  for (const scene of scenes) {
    if (scene.type !== "concept") continue;
    const steps = scene.diagram_steps || [];
    if (steps.length) {
      for (const step of steps) {
        const detail = String(step.detail || "").trim();
        out.push(detail);
      }
      break;
    }
  }
  // Align length with titles
  const titles = lessonExplainedTopics(lesson);
  while (out.length < titles.length) out.push("");
  return out.slice(0, titles.length);
}
'''
    v = v[:end] + helper + v[end:]
    vis.write_text(v)
    print('explainerVisuals helper added')
else:
    print('helper already present')

# Fix export canvas: more space after checkmark circle (pad + 48 instead of 42)
exp = Path("frontend/lib/reelExport.ts")
e = exp.read_text()
e2 = e.replace(
    'ctx.fillText(line, x + pad + 42, by + 20 + li * 18);',
    'ctx.fillText(line, x + pad + 52, by + 20 + li * 18);',
    1,
)
if e2 == e:
    print('WARN: export text x not updated')
else:
    exp.write_text(e2)
    print('export spacing updated')

print('done')
