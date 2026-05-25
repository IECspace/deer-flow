from __future__ import annotations

from dataclasses import replace
from typing import Any

from .models import GapQuestion, TestDesignModel


def apply_answers(model: TestDesignModel, answers: dict[str, Any]) -> TestDesignModel:
    """Merge user answers into model.

    Behavior:
    - store answered items into `assumptions` (as confirmed notes)
    - remove corresponding gap questions
    """

    answered_ids = {qid for qid, val in answers.items() if val is not None and str(val).strip()}
    remaining_gaps: list[GapQuestion] = [g for g in model.gaps if g.question_id not in answered_ids]

    new_assumptions = list(model.assumptions)
    for qid in answered_ids:
        val = answers[qid]
        new_assumptions.append(f"[confirmed:{qid}] {str(val).strip()}")

    return replace(model, gaps=remaining_gaps, assumptions=new_assumptions)


def answers_template(model: TestDesignModel) -> dict[str, str]:
    return {g.question_id: "" for g in model.gaps}

