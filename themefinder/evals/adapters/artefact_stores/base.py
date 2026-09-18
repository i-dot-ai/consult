"""ArtefactStorePort and local helper functions shared by artefact store adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, is_dataclass
from typing import Any

from eval_types import Case, CaseOutcome, RunReport, Score


class ArtefactStorePort(ABC):
    @abstractmethod
    def start_run(self, component: str, dataset: str) -> None | dict[str, Any]:
        """Initialise any per-run state before case recording begins."""

    @abstractmethod
    def record_case(self, outcome: CaseOutcome) -> None:
        """Persist or enqueue one case outcome for the active run."""

    @abstractmethod
    def finish_run(
        self,
        report: RunReport,
        *,
        engine_report: Any | None = None,
    ) -> dict[str, Any]:
        """Finalise the run and return the flat benchmark-compatible result dict."""


def _case_key(case: Case) -> str:
    question_part = case.metadata.get("question_part")
    if question_part:
        return str(question_part)
    return case.id


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, bool | int | float | str):
        return value

    if is_dataclass(value):
        return _json_safe(asdict(value))

    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}

    if isinstance(value, list | tuple | set):
        return [_json_safe(item) for item in value]

    return str(value)


def _serialise_case(case: Case) -> dict[str, Any]:
    return {
        "id": case.id,
        "inputs": _json_safe(case.inputs),
        "expected_output": _json_safe(case.expected_output),
        "metadata": _json_safe(case.metadata),
    }


def _serialise_score(score: Score) -> dict[str, Any]:
    return {
        "name": score.name,
        "value": score.value,
        "comment": score.comment,
    }


def _serialise_outcome(outcome: CaseOutcome) -> dict[str, Any]:
    return {
        "case": _serialise_case(outcome.case),
        "output": _json_safe(outcome.output),
        "scores": [_serialise_score(score) for score in outcome.scores],
        "error": outcome.error,
    }


def _flatten_run_report(report: RunReport) -> dict[str, Any]:
    results: dict[str, Any] = {}

    for outcome in report.outcomes:
        key = _case_key(outcome.case)
        results[f"{key}_output"] = _json_safe(outcome.output)

        for score in outcome.scores:
            results[f"{key}_{score.name}"] = score.value

    return results


def _build_results_payload(
    component: str,
    dataset: str,
    report: RunReport,
    *,
    recorded_outcomes: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    outcomes = recorded_outcomes or [
        _serialise_outcome(outcome) for outcome in report.outcomes
    ]

    return {
        "component": component,
        "dataset": dataset,
        "results": _flatten_run_report(report),
        "outcomes": outcomes,
        "errors": {
            _case_key(outcome.case): outcome.error
            for outcome in report.outcomes
            if outcome.error is not None
        },
    }
