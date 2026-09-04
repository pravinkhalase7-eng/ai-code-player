from __future__ import annotations

import re
from typing import Any

from sqlalchemy.orm import Session

from app.agents.orchestrator import evaluate_answer
from app.errors import AppError
from app.models.orm import QuizAttempt, QuizQuestion, UserConcept
from app.schemas.lesson import EvaluationResult
from app.services.execution.client import execute_in_sandbox
from app.services.progress_service import adjust_mastery

_NORMALIZE = re.compile(r"\s+")


def _norm(value: str) -> str:
    return _NORMALIZE.sub(" ", value.strip().lower())


def evaluate_quiz(
    db: Session,
    question_id: str,
    user_id: str,
    answer: int | str | None,
    code: str | None,
    hints_used: int,
) -> tuple[EvaluationResult, float | None]:
    question = db.get(QuizQuestion, question_id)
    if question is None:
        question = (
            db.query(QuizQuestion).filter(QuizQuestion.scene_id == question_id).one_or_none()
        )
    if question is None:
        raise AppError(404, "Quiz not found", "That question does not exist.", "not_found")

    payload: dict[str, Any] = question.payload or {}
    kind = question.kind
    status = "incorrect"
    explanation = payload.get("explanation") or "Let's look at this together."
    misconception = None

    if kind in {"multiple_choice", "predict_output", "find_the_bug"}:
        expected = payload.get("answer")
        if isinstance(answer, int) and answer == expected:
            status = "correct"
            explanation = payload.get("explanation") or "Exactly. That is the output of the loop."
        elif isinstance(answer, int):
            misconception = "The loop body runs while the condition is true, then increments."
            explanation = payload.get("explanation") or (
                "Not quite. Trace i from 0 and stop when the condition becomes false."
            )
    elif kind == "fill_in_code":
        expected = str(payload.get("answer") or payload.get("blank_token") or "i++")
        given = str(answer or "")
        if _norm(given) == _norm(expected) or _norm(given) in {"i++", "++i", "i += 1", "i=i+1"}:
            status = "correct"
            explanation = "i++ increases i after each iteration so the loop can finish."
        elif "i" in _norm(given):
            status = "partially_correct"
            misconception = "increment_syntax"
            explanation = "You are changing i, but the usual form here is i++."
        else:
            misconception = "missing_increment"
            explanation = "Without i++ the condition i < 5 stays true forever."
    elif kind in {"coding_challenge", "modify_code"}:
        language = payload.get("language") or "java"
        submitted = code or str(answer or "")
        if not submitted.strip():
            explanation = "Submit code so the sandbox can run it."
        else:
            result = execute_in_sandbox(language, submitted)
            if result.timed_out:
                status = "incorrect"
                misconception = "infinite_loop"
                explanation = (
                    "Execution stopped because the program exceeded the time limit. "
                    "If you removed the increment, i never reaches the stop condition."
                )
            elif result.compile_error:
                status = "incorrect"
                misconception = "compile_error"
                explanation = f"Compilation Error\n{result.stderr}"
            elif result.success:
                expected_lines = payload.get("expected_output") or []
                if expected_lines and result.stdout == expected_lines:
                    status = "correct"
                    explanation = "Your program produced the expected output."
                elif expected_lines and set(result.stdout) == set(expected_lines):
                    status = "partially_correct"
                    explanation = "The values appeared, but the order or count did not match."
                elif not expected_lines:
                    status = "correct"
                    explanation = "The sandbox ran your program successfully."
                else:
                    explanation = f"The sandbox printed {result.stdout}. That is not the target output."
            else:
                explanation = result.stderr or "The program did not run successfully."
    else:
        try:
            result = evaluate_answer(str(payload), str(answer or code or ""))
            db.add(
                QuizAttempt(
                    user_id=user_id,
                    question_id=question.id,
                    answer={"answer": answer, "code": code},
                    status=result.status,
                )
            )
            db.commit()
            mastery = adjust_mastery(db, user_id, "for_loop", result, hints_used)
            return result, mastery
        except Exception:
            status = "partially_correct"
            explanation = "Thanks. I saved your explanation for review."

    delta = 0.18 if status == "correct" else 0.05 if status == "partially_correct" else -0.08
    result = EvaluationResult(
        status=status,  # type: ignore[arg-type]
        misconception=misconception,
        explanation=explanation,
        next_action="continue" if status == "correct" else "reteach",
        mastery_delta=delta,
    )
    db.add(
        QuizAttempt(
            user_id=user_id,
            question_id=question.id,
            answer={"answer": answer, "code": code},
            status=status,
        )
    )
    db.commit()
    mastery = adjust_mastery(db, user_id, "for_loop", result, hints_used)
    return result, mastery
