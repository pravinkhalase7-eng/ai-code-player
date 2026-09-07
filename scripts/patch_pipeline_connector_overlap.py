from pathlib import Path

# --- MechanismBoard GenericStageBoard mini pipeline ---
mech = Path("frontend/components/player/MechanismBoard.tsx")
mt = mech.read_text()

old_pipe = '''        <div className="mechanism-mini-pipeline relative mx-auto w-full max-w-[22rem] shrink-0 px-2 pt-1">
          <div
            className="pointer-events-none absolute left-4 right-4 top-1/2 h-[2px] -translate-y-1/2 rounded-full bg-cyan-400/15"
            aria-hidden
          />
          <div
            className="pointer-events-none absolute left-4 top-1/2 h-[2px] -translate-y-1/2 rounded-full bg-gradient-to-r from-cyan-400/70 via-amber-300/80 to-cyan-300/50 transition-[width] duration-500 ease-out"
            style={{ width: `calc((100% - 2rem) * ${tokenPct / 100})` }}
            aria-hidden
          />
          <ol className="relative z-10 flex items-center justify-between gap-1">
            {steps.map((s, index) => {
              const isActive = index === safeActive;
              const isPast = index < safeActive;
              return (
                <li
                  key={`mini-${index}-${s.title}`}
                  className={cn(
                    "flex h-8 w-8 items-center justify-center rounded-full border text-[10px] font-extrabold transition-all duration-300",
                    isActive &&
                      "border-amber-300/80 bg-amber-400/25 text-amber-100 shadow-[0_0_16px_rgba(251,191,36,0.45)]",
                    isPast && !isActive && "border-cyan-300/50 bg-cyan-400/30 text-cyan-50",
                    !isActive && !isPast && "border-white/10 bg-white/5 text-cyan-200/35 opacity-45",
                  )}
                  title={s.title}
                >
                  {index + 1}
                </li>
              );
            })}
          </ol>
        </div>

        <div className="relative flex min-h-0 flex-1 flex-col justify-center px-0.5 pb-0.5">
          <div
            key={`stage-${safeActive}-${title}`}
            className="mechanism-stage-card relative mx-auto flex w-full max-w-[22rem] flex-col gap-3 rounded-2xl border border-cyan-300/45 bg-[rgba(8,51,68,0.82)] px-3.5 py-3.5 shadow-[0_0_0_1px_rgba(34,211,238,0.28),0_16px_40px_rgba(8,145,178,0.35)] backdrop-blur-md"
'''

new_pipe = '''        <div className="mechanism-mini-pipeline relative mx-auto w-full max-w-[22rem] shrink-0 px-3 pt-2 pb-1">
          {/* Track sits behind nodes; inset so caps don't poke past first/last circles */}
          <div
            className="pointer-events-none absolute left-5 right-5 top-1/2 z-0 h-[2px] -translate-y-1/2 rounded-full bg-cyan-400/20"
            aria-hidden
          />
          <div
            className="pointer-events-none absolute left-5 top-1/2 z-0 h-[2px] -translate-y-1/2 rounded-full bg-gradient-to-r from-cyan-400/80 via-amber-300/85 to-cyan-300/55 transition-[width] duration-500 ease-out"
            style={{ width: `calc((100% - 2.5rem) * ${tokenPct / 100})` }}
            aria-hidden
          />
          <ol className="relative z-10 flex items-center justify-between gap-2">
            {steps.map((s, index) => {
              const isActive = index === safeActive;
              const isPast = index < safeActive;
              return (
                <li
                  key={`mini-${index}-${s.title}`}
                  className={cn(
                    // Opaque fill + board-colored ring masks the connector under each circle
                    "relative z-10 flex h-9 w-9 items-center justify-center rounded-full border-2 text-[11px] font-extrabold transition-all duration-300 ring-4 ring-[#031018]",
                    isActive &&
                      "border-amber-300 bg-[#3b2a0a] text-amber-100 shadow-[0_0_18px_rgba(251,191,36,0.5)]",
                    isPast && !isActive && "border-cyan-300 bg-[#0a3a45] text-cyan-50",
                    !isActive && !isPast && "border-white/20 bg-[#0a1c24] text-cyan-200/55",
                  )}
                  title={s.title}
                >
                  {index + 1}
                </li>
              );
            })}
          </ol>
        </div>

        <div className="relative flex min-h-0 flex-1 flex-col justify-center px-1 pb-1 pt-1">
          <div
            key={`stage-${safeActive}-${title}`}
            className="mechanism-stage-card relative mx-auto flex w-full max-w-[22rem] flex-col gap-3.5 rounded-2xl border border-cyan-300/45 bg-[rgba(8,51,68,0.82)] px-4 py-4 shadow-[0_0_0_1px_rgba(34,211,238,0.28),0_16px_40px_rgba(8,145,178,0.35)] backdrop-blur-md"
'''

if old_pipe not in mt:
    raise SystemExit('MechanismBoard pipeline block missing')
mt = mt.replace(old_pipe, new_pipe, 1)

# Outer board padding + gap
mt = mt.replace(
    'className="mechanism-board relative flex min-h-0 flex-1 flex-col overflow-hidden rounded-2xl border border-cyan-200/25 bg-[#031018]/94 p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]"',
    'className="mechanism-board relative flex min-h-0 flex-1 flex-col overflow-hidden rounded-2xl border border-cyan-200/25 bg-[#031018]/94 p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]"',
    1,
)
mt = mt.replace(
    '<div className="relative z-10 flex min-h-0 flex-1 flex-col gap-3">\n        <div className="mechanism-mini-pipeline',
    '<div className="relative z-10 flex min-h-0 flex-1 flex-col gap-5">\n        <div className="mechanism-mini-pipeline',
    1,
)
mech.write_text(mt)
print('MechanismBoard ok')

# --- ExplainerFlow similar ---
ef = Path("frontend/components/player/ExplainerFlow.tsx")
et = ef.read_text()

old_ef = '''        <div className="explainer-mini-pipeline relative mx-auto w-full max-w-[22rem] shrink-0 px-2 pt-1">
          <div className="pointer-events-none absolute left-4 right-4 top-1/2 h-[2px] -translate-y-1/2 rounded-full bg-cyan-400/15" aria-hidden />
          <div
            className="pointer-events-none absolute left-4 top-1/2 h-[2px] -translate-y-1/2 rounded-full bg-gradient-to-r from-cyan-400/70 via-amber-300/80 to-cyan-300/50 transition-[width] duration-500 ease-out"
            style={{ width: `calc((100% - 2rem) * ${tokenPct / 100})` }}
            aria-hidden
          />
'''

# Need fuller replace including token + ol - read if token exists
if old_ef not in et:
    # try without exact match - print snippet
    i = et.find('explainer-mini-pipeline')
    print('ExplainerFlow snippet:\\n', et[i:i+900])
    raise SystemExit('ExplainerFlow pipeline start missing')

# Replace a larger block including nodes
idx = et.find('        <div className="explainer-mini-pipeline')
end_marker = '        {/* ONE large active stage card */}'
end = et.find(end_marker, idx)
if end < 0:
    raise SystemExit('ExplainerFlow stage marker missing')

new_ef_block = '''        <div className="explainer-mini-pipeline relative mx-auto w-full max-w-[22rem] shrink-0 px-3 pt-2 pb-1">
          <div className="pointer-events-none absolute left-5 right-5 top-1/2 z-0 h-[2px] -translate-y-1/2 rounded-full bg-cyan-400/20" aria-hidden />
          <div
            className="pointer-events-none absolute left-5 top-1/2 z-0 h-[2px] -translate-y-1/2 rounded-full bg-gradient-to-r from-cyan-400/80 via-amber-300/85 to-cyan-300/55 transition-[width] duration-500 ease-out"
            style={{ width: `calc((100% - 2.5rem) * ${tokenPct / 100})` }}
            aria-hidden
          />
          <div
            className="explainer-token pointer-events-none absolute top-1/2 z-20 transition-[left] duration-500 ease-out"
            style={{ left: `calc(1.25rem + (100% - 2.5rem) * ${tokenPct / 100})`, transform: "translate(-50%, -50%)" }}
            aria-hidden
          >
            <span className="explainer-token-orb" />
          </div>
          <ol className="relative z-10 flex items-center justify-between gap-2">
            {steps.map((s, index) => {
              const Icon = icons[index] || Hexagon;
              const visible = visibleCount > index;
              const isActive = active === index && visible;
              const isPast = visible && index < active;
              const isFuture = !visible || index > active;
              return (
                <li
                  key={`mini-${index}-${s.title}`}
                  className={cn(
                    "explainer-mini-node relative z-10 flex h-9 w-9 items-center justify-center rounded-full border-2 transition-all duration-300 ring-4 ring-[#031018]",
                    isActive && "is-active border-amber-300 bg-[#3b2a0a] text-amber-100 shadow-[0_0_18px_rgba(251,191,36,0.5)]",
                    isPast && !isActive && "border-cyan-300 bg-[#0a3a45] text-cyan-50",
                    isFuture && !isActive && "border-white/20 bg-[#0a1c24] text-cyan-200/55",
                  )}
                  title={s.title}
                >
                  <Icon className={cn("h-3.5 w-3.5", isActive && "animate-pulse")} strokeWidth={2.4} />
                </li>
              );
            })}
          </ol>
        </div>

'''
et = et[:idx] + new_ef_block + et[end:]

# breathing space on explainer flow outer
et = et.replace(
    '<div className="relative z-10 flex min-h-0 flex-1 flex-col gap-3">\n        {/* Mini pipeline */}',
    '<div className="relative z-10 flex min-h-0 flex-1 flex-col gap-5">\n        {/* Mini pipeline */}',
    1,
)
# stage card padding if present
et = et.replace(
    'px-3.5 py-3.5 shadow-[0_0_0_1px_rgba(34,211,238,0.28),0_16px_40px_rgba(8,145,178,0.35)] backdrop-blur-md"',
    'px-4 py-4 shadow-[0_0_0_1px_rgba(34,211,238,0.28),0_16px_40px_rgba(8,145,178,0.35)] backdrop-blur-md"',
    1,
)
ef.write_text(et)
print('ExplainerFlow ok')
print('done')
