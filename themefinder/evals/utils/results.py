"""Helpers for reading the results payload that the local artefact store writes."""

from typing import Any

from constants import EVALUATOR_ERROR_PREFIX


def count_errors(payload: dict[str, Any]) -> int:
    """Count failed cases and scores an evaluator zeroed after an exception.

    Evaluator failures are recorded as 0.0 scores with an error comment, so without
    this they look like genuinely low scores. A flat payload without `outcomes` has no
    per-case detail, so it counts as zero errors.
    """
    errors = 0
    for outcome in payload.get("outcomes", []):
        errors += bool(outcome.get("error"))
        errors += sum(
            str(score.get("comment", "")).startswith(EVALUATOR_ERROR_PREFIX)
            for score in outcome.get("scores", [])
        )
    return errors
