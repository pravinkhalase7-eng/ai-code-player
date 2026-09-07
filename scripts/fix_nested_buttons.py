from pathlib import Path

path = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder/frontend/components/dashboard/Dashboard.tsx")
text = path.read_text()
old = '''                <div key={lesson.lesson_id} className="relative w-full">
                  <button
                    type="button"
                    onClick={() => router.push(`/learn/${lesson.lesson_id}`)}
                    className="w-full text-left"
                    disabled={deleting}
                  >
                    <Card className="overflow-hidden p-0 transition hover:border-amber-300/30">
                      {lesson.format === "reel" && lesson.thumbnail_url ? (
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
new = '''                <div key={lesson.lesson_id} className="relative w-full">
                  <button
                    type="button"
                    onClick={() => router.push(`/learn/${lesson.lesson_id}`)}
                    className="w-full text-left"
                    disabled={deleting}
                  >
                    <Card className="overflow-hidden p-0 transition hover:border-amber-300/30">
                      {lesson.format === "reel" && lesson.thumbnail_url ? (
                        <div className="relative h-36 w-full overflow-hidden bg-zinc-900 sm:h-44">
                          <img src={lesson.thumbnail_url} alt="" className="h-full w-full object-cover" />
                          <span className="absolute left-3 top-3 rounded-full bg-amber-400 px-2 py-0.5 text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-950">
                            {lesson.reel_seconds ? `${lesson.reel_seconds}s` : "Short"}
                          </span>
                        </div>
                      ) : lesson.format === "reel" ? (
                        <div className="relative flex h-28 w-full items-center justify-center bg-zinc-900/80 sm:h-32">
                          <span className="text-xs text-zinc-500">No thumbnail yet</span>
                        </div>
                      ) : null}
'''
if old not in text:
    raise SystemExit("block1 not found")
text = text.replace(old, new, 1)

old_del = '''                  <button
                    type="button"
                    aria-label={lesson.format === "reel" ? "Delete this short" : "Delete this lesson"}
                    title={lesson.format === "reel" ? "Delete this short" : "Delete this lesson"}
                    disabled={deleting}
                    onClick={(event) => void removeLesson(lesson, event)}
                    className="absolute right-2 top-2 z-10 inline-flex h-11 w-11 items-center justify-center rounded-full border border-white/15 bg-zinc-950/80 text-zinc-200 shadow-lg backdrop-blur transition hover:border-red-300/50 hover:bg-red-500/20 hover:text-red-100 disabled:opacity-50"
                  >
                    <Trash2 className="h-5 w-5" strokeWidth={2.25} />
                  </button>
'''
new_del = '''                  {lesson.format === "reel" ? (
                    <div className="absolute bottom-[7.5rem] right-2 z-10 flex gap-1.5 sm:bottom-[8.5rem]">
                      {lesson.thumbnail_url ? (
                        <button
                          type="button"
                          title="View thumbnail fullscreen"
                          aria-label="View thumbnail fullscreen"
                          className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-white/20 bg-zinc-950/80 text-white shadow-lg backdrop-blur hover:border-cyan-300/50 hover:bg-cyan-500/20"
                          onClick={(event) => openThumbPreview(lesson, event)}
                        >
                          <Expand className="h-4 w-4" />
                        </button>
                      ) : null}
                      <button
                        type="button"
                        title="Regenerate thumbnail"
                        aria-label="Regenerate thumbnail"
                        disabled={thumbBusyId === lesson.lesson_id}
                        className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-white/20 bg-zinc-950/80 text-white shadow-lg backdrop-blur hover:border-amber-300/50 hover:bg-amber-500/20 disabled:opacity-50"
                        onClick={(event) => void regenThumbnail(lesson, event)}
                      >
                        {lesson.thumbnail_url ? (
                          <RefreshCw className={`h-4 w-4 ${thumbBusyId === lesson.lesson_id ? "animate-spin" : ""}`} />
                        ) : (
                          <ImageIcon className={`h-4 w-4 ${thumbBusyId === lesson.lesson_id ? "animate-spin" : ""}`} />
                        )}
                      </button>
                    </div>
                  ) : null}
                  <button
                    type="button"
                    aria-label={lesson.format === "reel" ? "Delete this short" : "Delete this lesson"}
                    title={lesson.format === "reel" ? "Delete this short" : "Delete this lesson"}
                    disabled={deleting}
                    onClick={(event) => void removeLesson(lesson, event)}
                    className="absolute right-2 top-2 z-10 inline-flex h-11 w-11 items-center justify-center rounded-full border border-white/15 bg-zinc-950/80 text-zinc-200 shadow-lg backdrop-blur transition hover:border-red-300/50 hover:bg-red-500/20 hover:text-red-100 disabled:opacity-50"
                  >
                    <Trash2 className="h-5 w-5" strokeWidth={2.25} />
                  </button>
'''
if old_del not in text:
    raise SystemExit("delete block not found")
text = text.replace(old_del, new_del, 1)
path.write_text(text)
print("fixed")
