#!/usr/bin/env python3
"""Wire reel_mode through router, lesson_service, tasks, jobs; fix plan_lesson precedence."""
from pathlib import Path

ROOT = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder")

# ---- fix orchestrator plan_lesson mode precedence ----
orch = ROOT / "backend/app/agents/orchestrator.py"
ot = orch.read_text(encoding="utf-8")

old_msg = '''        if mode == "explainer" or (requires_code is False and mode == "explainer"):
            message += (
                " This is an EXPLAINER reel: requires_code=false, reel_mode=explainer. "
                "Do NOT plan a program. Teach HOW it works with intro, concept diagram_steps, and summary only."
            )
        elif mode == "info" or (requires_code is False and mode != "explainer"):
            message += (
                " This is an INFO reel: requires_code=false, reel_mode=info. "
                "Do NOT plan a program. Teach the idea with intro, concept bullets, and summary only."
            )
        elif mode == "code" or requires_code is True:
            message += " This is a CODE short: requires_code=true, reel_mode=code. Include a runnable example."'''

new_msg = '''        if mode == "explainer":
            message += (
                " This is an EXPLAINER reel: requires_code=false, reel_mode=explainer. "
                "Do NOT plan a program. Teach HOW it works with intro, concept diagram_steps, and summary only."
            )
        elif mode == "code" or requires_code is True:
            message += " This is a CODE short: requires_code=true, reel_mode=code. Include a runnable example."
        elif mode == "info" or requires_code is False:
            message += (
                " This is an INFO reel: requires_code=false, reel_mode=info. "
                "Do NOT plan a program. Teach the idea with intro, concept bullets, and summary only."
            )'''

if old_msg not in ot:
    raise SystemExit("message branch missing")
ot = ot.replace(old_msg, new_msg, 1)

old_assign = '''    if fmt == "reel":
        if mode == "explainer" or (requires_code is False and mode == "explainer"):
            plan.requires_code = False
            plan.reel_mode = "explainer"
        elif mode == "info" or (requires_code is False and mode != "explainer"):
            plan.requires_code = False
            plan.reel_mode = "info"
        elif mode == "code" or requires_code is True:
            plan.requires_code = True
            plan.reel_mode = "code"
        elif not inferred:
            plan.requires_code = False
            plan.reel_mode = "info"
        else:
            plan.requires_code = bool(getattr(plan, "requires_code", True))
            plan.reel_mode = "code" if plan.requires_code else "info"
    else:
        plan.requires_code = True
        plan.reel_mode = None
    return plan'''

new_assign = '''    if fmt == "reel":
        if mode == "explainer":
            plan.requires_code = False
            plan.reel_mode = "explainer"
        elif mode == "code" or requires_code is True:
            plan.requires_code = True
            plan.reel_mode = "code"
        elif mode == "info" or requires_code is False:
            plan.requires_code = False
            plan.reel_mode = "info"
        elif not inferred:
            plan.requires_code = False
            plan.reel_mode = "info"
        else:
            plan.requires_code = bool(getattr(plan, "requires_code", True))
            plan.reel_mode = "code" if plan.requires_code else "info"
    else:
        plan.requires_code = True
        plan.reel_mode = None
    return plan'''

if old_assign not in ot:
    raise SystemExit("assign branch missing")
ot = ot.replace(old_assign, new_assign, 1)

# Also simplify generate planner check
ot = ot.replace(
    '    if is_reel and (plan_mode == "explainer" or (not plan.requires_code and plan_mode == "explainer")):',
    '    if is_reel and plan_mode == "explainer":',
    1,
)

orch.write_text(ot, encoding="utf-8")
print("orchestrator precedence ok")

# ---- router.py ----
router = ROOT / "backend/app/api/v1/router.py"
rt = router.read_text(encoding="utf-8")
if "reel_mode=payload.reel_mode" not in rt:
    rt = rt.replace(
        "        requires_code=payload.requires_code,\n"
        "    )\n"
        '    return LessonCreateResponse(lesson_id=lesson_id, status="queued", job_id=job_id)',
        "        requires_code=payload.requires_code,\n"
        "        reel_mode=payload.reel_mode,\n"
        "    )\n"
        '    return LessonCreateResponse(lesson_id=lesson_id, status="queued", job_id=job_id)',
        1,
    )
    # pending lesson: stamp reel_mode
    if 'reel_mode=(row.lesson_json or {}).get("reel_mode")' not in rt:
        rt = rt.replace(
            "            requires_code=not explain,\n"
            "            scenes=[",
            "            requires_code=not explain,\n"
            '            reel_mode=(row.lesson_json or {}).get("reel_mode"),\n'
            "            scenes=[",
            1,
        )
    router.write_text(rt, encoding="utf-8")
    print("router ok")
else:
    print("router already wired")

# ---- lesson_service.py ----
ls = ROOT / "backend/app/services/lesson_service.py"
lt = ls.read_text(encoding="utf-8")

# queue_lesson
if "reel_mode: str | None = None" not in lt[lt.index("def queue_lesson"): lt.index("def persist_lesson")]:
    lt = lt.replace(
        '''def queue_lesson(
    db: Session,
    topic: str,
    language: str,
    level: str,
    user_id: str | None,
    format: str = "lesson",
    spoken_language: str = "en",
    reel_seconds: int = 30,
    requires_code: bool | None = None,
) -> tuple[str, str]:''',
        '''def queue_lesson(
    db: Session,
    topic: str,
    language: str,
    level: str,
    user_id: str | None,
    format: str = "lesson",
    spoken_language: str = "en",
    reel_seconds: int = 30,
    requires_code: bool | None = None,
    reel_mode: str | None = None,
) -> tuple[str, str]:''',
        1,
    )
    lt = lt.replace(
        '            **({"requires_code": requires_code} if requires_code is not None else {}),\n'
        "        },\n"
        "    )\n"
        "    db.add(row)\n",
        '            **({"requires_code": requires_code} if requires_code is not None else {}),\n'
        '            **({"reel_mode": reel_mode} if reel_mode else {}),\n'
        "        },\n"
        "    )\n"
        "    db.add(row)\n",
        1,
    )
    lt = lt.replace(
        '            **({"requires_code": requires_code} if requires_code is not None else {}),\n'
        "        },\n"
        "    )\n"
        '    enqueue(job.id, "lesson_generation")\n',
        '            **({"requires_code": requires_code} if requires_code is not None else {}),\n'
        '            **({"reel_mode": reel_mode} if reel_mode else {}),\n'
        "        },\n"
        "    )\n"
        '    enqueue(job.id, "lesson_generation")\n',
        1,
    )
    print("queue_lesson ok")

# build_lesson
if "reel_mode: str | None = None" not in lt[lt.index("def build_lesson"): lt.index("def build_lesson") + 400]:
    lt = lt.replace(
        '''def build_lesson(
    db: Session,
    lesson_id: str,
    topic: str,
    language: str,
    level: str,
    format: str = "lesson",
    spoken_language: str = "en",
    reel_seconds: int = 30,
    requires_code: bool | None = None,
) -> Lesson:''',
        '''def build_lesson(
    db: Session,
    lesson_id: str,
    topic: str,
    language: str,
    level: str,
    format: str = "lesson",
    spoken_language: str = "en",
    reel_seconds: int = 30,
    requires_code: bool | None = None,
    reel_mode: str | None = None,
) -> Lesson:''',
        1,
    )
    lt = lt.replace(
        '''    if requires_code is None and isinstance(row.lesson_json, dict) and "requires_code" in row.lesson_json:
        requires_code = bool(row.lesson_json.get("requires_code"))
    plan = plan_lesson(
        topic,
        language,
        level,
        format=format,
        spoken_language=spoken_language,
        reel_seconds=reel_seconds,
        requires_code=requires_code,
    )''',
        '''    if requires_code is None and isinstance(row.lesson_json, dict) and "requires_code" in row.lesson_json:
        requires_code = bool(row.lesson_json.get("requires_code"))
    if not reel_mode and isinstance(row.lesson_json, dict):
        reel_mode = row.lesson_json.get("reel_mode")
    plan = plan_lesson(
        topic,
        language,
        level,
        format=format,
        spoken_language=spoken_language,
        reel_seconds=reel_seconds,
        requires_code=requires_code,
        reel_mode=reel_mode,
    )''',
        1,
    )
    print("build_lesson ok")

# list_recent_lessons include reel_mode
if '"reel_mode"' not in lt[lt.index("def list_recent_lessons"): lt.index("def delete_lesson")]:
    lt = lt.replace(
        '                "reel_seconds": (row.lesson_json or {}).get("reel_seconds") or 30,\n'
        "            }\n"
        "        )\n"
        "    return results",
        '                "reel_seconds": (row.lesson_json or {}).get("reel_seconds") or 30,\n'
        '                "reel_mode": (row.lesson_json or {}).get("reel_mode"),\n'
        '                "requires_code": (row.lesson_json or {}).get("requires_code"),\n'
        "            }\n"
        "        )\n"
        "    return results",
        1,
    )
    print("list_recent ok")

ls.write_text(lt, encoding="utf-8")

# ---- tasks.py ----
tasks = ROOT / "backend/app/workers/tasks.py"
tt = tasks.read_text(encoding="utf-8")
if 'payload.get("reel_mode")' not in tt:
    tt = tt.replace(
        '                payload.get("requires_code"),\n'
        "            )",
        '                payload.get("requires_code"),\n'
        '                payload.get("reel_mode"),\n'
        "            )",
        1,
    )
    tasks.write_text(tt, encoding="utf-8")
    print("tasks ok")
else:
    print("tasks already wired")

# ---- jobs.py ----
jobs = ROOT / "backend/app/services/jobs.py"
jt = jobs.read_text(encoding="utf-8")
if '"reel_mode"' not in jt:
    jt = jt.replace(
        '''                **(
                    {"requires_code": (row.lesson_json or {}).get("requires_code")}
                    if isinstance(row.lesson_json, dict) and "requires_code" in row.lesson_json
                    else {}
                ),
            },
        )''',
        '''                **(
                    {"requires_code": (row.lesson_json or {}).get("requires_code")}
                    if isinstance(row.lesson_json, dict) and "requires_code" in row.lesson_json
                    else {}
                ),
                **(
                    {"reel_mode": (row.lesson_json or {}).get("reel_mode")}
                    if isinstance(row.lesson_json, dict) and (row.lesson_json or {}).get("reel_mode")
                    else {}
                ),
            },
        )''',
        1,
    )
    jobs.write_text(jt, encoding="utf-8")
    print("jobs ok")
else:
    print("jobs already wired")

print("wiring done")
