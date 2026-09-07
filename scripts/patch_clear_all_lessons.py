from pathlib import Path

ROOT = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder")

# --- lesson_service.py ---
svc = ROOT / "backend/app/services/lesson_service.py"
text = svc.read_text()
if "def delete_all_lessons" not in text:
    insert = '''

def delete_all_lessons(db: Session) -> dict[str, int]:
    """Remove every lesson and related rows; clear generated audio files."""
    from pathlib import Path as _Path

    lesson_ids = [lid for (lid,) in db.query(LessonRow.id).all()]
    count = len(lesson_ids)
    if lesson_ids:
        question_ids = [
            qid
            for (qid,) in db.query(QuizQuestion.id).filter(QuizQuestion.lesson_id.in_(lesson_ids)).all()
        ]
        if question_ids:
            db.query(QuizAttempt).filter(QuizAttempt.question_id.in_(question_ids)).delete(synchronize_session=False)
        db.query(QuizQuestion).filter(QuizQuestion.lesson_id.in_(lesson_ids)).delete(synchronize_session=False)
        db.query(LessonProgress).filter(LessonProgress.lesson_id.in_(lesson_ids)).delete(synchronize_session=False)
        db.query(CodeExample).filter(CodeExample.lesson_id.in_(lesson_ids)).delete(synchronize_session=False)
        db.query(CodeExecution).filter(CodeExecution.lesson_id.in_(lesson_ids)).delete(synchronize_session=False)
        db.query(LessonSceneRow).filter(LessonSceneRow.lesson_id.in_(lesson_ids)).delete(synchronize_session=False)
        db.query(LessonRow).delete(synchronize_session=False)
        db.commit()

    audio_removed = 0
    audio_dir = _Path(__file__).resolve().parents[2] / "storage" / "audio"
    if audio_dir.is_dir():
        for path in audio_dir.rglob("*"):
            if path.is_file():
                try:
                    path.unlink()
                    audio_removed += 1
                except OSError:
                    pass

    return {"lessons": count, "audio_files": audio_removed}

'''
    marker = "def delete_lesson(db: Session, lesson_id: str) -> None:"
    if marker not in text:
        raise SystemExit("delete_lesson not found")
    # insert after delete_lesson function — find end of delete_lesson (db.commit() then blank then def update)
    anchor = "    db.delete(row)\n    db.commit()\n\n\ndef update_reel_script("
    if anchor not in text:
        # try single newline
        anchor = "    db.delete(row)\n    db.commit()\n\ndef update_reel_script("
        if anchor not in text:
            raise SystemExit("delete_lesson end not found")
        text = text.replace(
            anchor,
            "    db.delete(row)\n    db.commit()\n" + insert + "\ndef update_reel_script(",
            1,
        )
    else:
        text = text.replace(
            anchor,
            "    db.delete(row)\n    db.commit()\n" + insert + "\ndef update_reel_script(",
            1,
        )
    svc.write_text(text)
    print("lesson_service: delete_all_lessons added")
else:
    print("lesson_service: already has delete_all_lessons")

# --- router.py ---
router = ROOT / "backend/app/api/v1/router.py"
rt = router.read_text()
if "delete_all_lessons" not in rt:
    rt = rt.replace(
        "from app.services.lesson_service import (\n    delete_lesson,\n",
        "from app.services.lesson_service import (\n    delete_all_lessons,\n    delete_lesson,\n",
        1,
    )
    endpoint = '''

@router.delete("/lessons")
def remove_all_lessons(db: Session = Depends(get_db)) -> dict:
    result = delete_all_lessons(db)
    return {"ok": True, **result}

'''
    marker = '@router.delete("/lesson/{lesson_id}")\ndef remove_lesson(lesson_id: str, db: Session = Depends(get_db)) -> dict:\n    delete_lesson(db, lesson_id)\n    return {"ok": True, "lesson_id": lesson_id}\n'
    if marker not in rt:
        raise SystemExit("remove_lesson endpoint not found")
    rt = rt.replace(marker, marker + endpoint, 1)
    router.write_text(rt)
    print("router: DELETE /lessons added")
else:
    print("router: already has delete_all")

# --- api.ts ---
api = ROOT / "frontend/lib/api.ts"
at = api.read_text()
if "deleteAllLessons" not in at:
    at = at.replace(
        '''export function deleteLesson(lessonId: string) {
  return request<{ ok: boolean; lesson_id: string }>(`/api/v1/lesson/${lessonId}`, {
    method: "DELETE",
  });
}
''',
        '''export function deleteLesson(lessonId: string) {
  return request<{ ok: boolean; lesson_id: string }>(`/api/v1/lesson/${lessonId}`, {
    method: "DELETE",
  });
}

export function deleteAllLessons() {
  return request<{ ok: boolean; lessons: number; audio_files: number }>("/api/v1/lessons", {
    method: "DELETE",
  });
}
''',
        1,
    )
    api.write_text(at)
    print("api.ts: deleteAllLessons added")
else:
    print("api.ts: already has deleteAllLessons")

# --- Dashboard.tsx ---
dash = ROOT / "frontend/components/dashboard/Dashboard.tsx"
dt = dash.read_text()
if "clearAllLessons" not in dt and "deleteAllLessons" not in dt.split("from")[0] + dt:
    pass

dt = dash.read_text()
if "deleteAllLessons" not in dt:
    dt = dt.replace(
        'import { createLesson, deleteLesson, getHealth, listLessons } from "@/lib/api";',
        'import { createLesson, deleteAllLessons, deleteLesson, getHealth, listLessons } from "@/lib/api";',
        1,
    )
    dt = dt.replace(
        '  const [deletingId, setDeletingId] = useState("");\n',
        '  const [deletingId, setDeletingId] = useState("");\n  const [clearingAll, setClearingAll] = useState(false);\n',
        1,
    )
    # add clearAll after removeLesson
    old_fn = '''  async function removeLesson(lesson: LessonSummary, event: MouseEvent) {
    event.stopPropagation();
    event.preventDefault();
    const kind = lesson.format === "reel" ? "short" : "lesson";
    if (!window.confirm(`Delete this ${kind}?`)) return;
    setDeletingId(lesson.lesson_id);
    setError("");
    try {
      await deleteLesson(lesson.lesson_id);
      setLessons((current) => current.filter((item) => item.lesson_id !== lesson.lesson_id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not delete the lesson");
    } finally {
      setDeletingId("");
    }
  }
'''
    new_fn = '''  async function removeLesson(lesson: LessonSummary, event: MouseEvent) {
    event.stopPropagation();
    event.preventDefault();
    const kind = lesson.format === "reel" ? "short" : "lesson";
    if (!window.confirm(`Delete this ${kind}?`)) return;
    setDeletingId(lesson.lesson_id);
    setError("");
    try {
      await deleteLesson(lesson.lesson_id);
      setLessons((current) => current.filter((item) => item.lesson_id !== lesson.lesson_id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not delete the lesson");
    } finally {
      setDeletingId("");
    }
  }

  async function clearAllLessons() {
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
    if old_fn not in dt:
        raise SystemExit("removeLesson block not found")
    dt = dt.replace(old_fn, new_fn, 1)

    old_header = '''      <section>
        <div className="mb-4 flex items-center gap-2 text-zinc-300">
          <Sparkles className="h-4 w-4 text-amber-300" />
          Continue Learning
        </div>
'''
    new_header = '''      <section>
        <div className="mb-4 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-zinc-300">
            <Sparkles className="h-4 w-4 text-amber-300" />
            Continue Learning
          </div>
          {lessons.length > 0 ? (
            <button
              type="button"
              onClick={() => void clearAllLessons()}
              disabled={clearingAll || Boolean(deletingId)}
              className="inline-flex items-center gap-1.5 rounded-full border border-red-300/30 bg-red-500/10 px-3 py-1.5 text-xs font-semibold text-red-200 transition hover:border-red-300/50 hover:bg-red-500/20 disabled:opacity-50"
            >
              <Trash2 className="h-3.5 w-3.5" />
              {clearingAll ? "Clearing..." : "Clear all"}
            </button>
          ) : null}
        </div>
'''
    if old_header not in dt:
        raise SystemExit("Continue Learning header not found")
    dt = dt.replace(old_header, new_header, 1)
    dash.write_text(dt)
    print("Dashboard: Clear all button added")
else:
    print("Dashboard: already wired")

print("done")
