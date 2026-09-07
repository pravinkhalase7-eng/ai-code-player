#!/usr/bin/env python3
"""Polish ExplainerFlow layout: dedicated spine gutter + valid Tailwind duration."""
from pathlib import Path

path = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder/frontend/components/player/ExplainerFlow.tsx")
text = path.read_text(encoding="utf-8")

old = '''        <div className="relative mx-auto w-full max-w-[22rem]">
          {/* Vertical spine + traveling token */}
          <div
            className="pointer-events-none absolute left-[1.35rem] top-3 bottom-3 w-8"
            aria-hidden
          >'''
new = '''        <div className="relative mx-auto w-full max-w-[22rem] pl-5">
          {/* Vertical spine + traveling token (gutter left of cards) */}
          <div
            className="pointer-events-none absolute left-0 top-3 bottom-3 w-5"
            aria-hidden
          >'''
if old not in text:
    raise SystemExit("layout block missing")
text = text.replace(old, new, 1)
text = text.replace("transition-all duration-400", "transition-all duration-300", 1)

# Hide chevron under badge when we have spine token — keep subtle only between nodes via CSS already
# Move badge row: drop chevron from under badge to reduce clutter with spine
old_chev = '''                    <span
                      className={cn(
                        "explainer-step-badge inline-flex h-7 w-7 items-center justify-center rounded-full text-[11px] font-extrabold",
                        isActive
                          ? "bg-amber-400 text-zinc-950 shadow-[0_0_18px_rgba(251,191,36,0.55)]"
                          : "bg-cyan-400/25 text-cyan-100",
                      )}
                    >
                      {index + 1}
                    </span>
                    {index < steps.length - 1 ? (
                      <span className={cn("explainer-chevron mt-1", visible && "is-visible")} aria-hidden>
                        <ChevronDown className="h-3.5 w-3.5 text-cyan-300/70" strokeWidth={2.5} />
                      </span>
                    ) : null}
                  </div>'''
new_chev = '''                    <span
                      className={cn(
                        "explainer-step-badge inline-flex h-7 w-7 items-center justify-center rounded-full text-[11px] font-extrabold",
                        isActive
                          ? "bg-amber-400 text-zinc-950 shadow-[0_0_18px_rgba(251,191,36,0.55)]"
                          : "bg-cyan-400/25 text-cyan-100",
                      )}
                    >
                      {index + 1}
                    </span>
                  </div>'''
if old_chev not in text:
    raise SystemExit("chevron block missing")
text = text.replace(old_chev, new_chev, 1)

# Remove unused ChevronDown import if no longer used
if "ChevronDown" not in text.split("from \"lucide-react\"")[0].split("import {")[-1] and False:
    pass
if "ChevronDown" in text and text.count("ChevronDown") == 1:
    text = text.replace("  ChevronDown,\n", "", 1)
elif text.count("ChevronDown") == 2:
    # still in import + maybe elsewhere — if only import left after remove usage
    pass

# After removing usage, only import remains → strip it
if "ChevronDown" in text and "<ChevronDown" not in text:
    text = text.replace("  ChevronDown,\n", "", 1)

path.write_text(text, encoding="utf-8")
print("polish ok")
