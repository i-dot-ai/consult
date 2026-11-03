"""Helpers for serialising, reading, and checking evaluation results."""

from dataclasses import asdict, is_dataclass
from typing import Any

from constants import EVALUATOR_ERROR_PREFIX
from eval_types import CaseOutcome, RunReport
from utils import stats


def json_safe(value: Any) -> Any:
    if value is None or isinstance(value, bool | int | float | str):
        return value

    if is_dataclass(value):
        return json_safe(asdict(value))

    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}

    if isinstance(value, list | tuple | set):
        return [json_safe(item) for item in value]

    return str(value)


def serialise_outcome(outcome: CaseOutcome) -> dict[str, Any]:
    """Serialise every dataclass field so new fields need no custom handling."""
    return json_safe(outcome)


def flatten_run_report(report: RunReport) -> dict[str, Any]:
    results: dict[str, Any] = {}

    for outcome in report.outcomes:
        key = report.outcome_key(outcome)
        results[f"{key}_output"] = json_safe(outcome.output)

        for score in outcome.scores:
            results[f"{key}_{score.name}"] = score.value

    if report.repeated:
        results["aggregate"] = stats.aggregate(report.outcomes)

    if report.metrics is not None:
        results["metrics"] = json_safe(report.metrics)

    return results


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
