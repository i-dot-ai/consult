"""ArtefactStorePort: the contract for artefact stores, plus the serialising and
run-aggregation helpers every store shares."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import asdict, is_dataclass
from itertools import combinations
from statistics import mean, stdev
from typing import Any

from eval_types import Case, CaseOutcome, RunReport, Score

CONSISTENCY_METRIC = "output_consistency"


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

    @staticmethod
    def case_key(case: Case) -> str:
        question_part = case.metadata.get("question_part")
        if question_part:
            return str(question_part)
        return case.id

    @classmethod
    def json_safe(cls, value: Any) -> Any:
        if value is None or isinstance(value, bool | int | float | str):
            return value

        if is_dataclass(value):
            return cls.json_safe(asdict(value))

        if isinstance(value, dict):
            return {str(key): cls.json_safe(item) for key, item in value.items()}

        if isinstance(value, list | tuple | set):
            return [cls.json_safe(item) for item in value]

        return str(value)

    @classmethod
    def serialise_case(cls, case: Case) -> dict[str, Any]:
        return {
            "id": case.id,
            "inputs": cls.json_safe(case.inputs),
            "expected_output": cls.json_safe(case.expected_output),
            "metadata": cls.json_safe(case.metadata),
        }

    @staticmethod
    def serialise_score(score: Score) -> dict[str, Any]:
        return {
            "name": score.name,
            "value": score.value,
            "comment": score.comment,
        }

    @classmethod
    def serialise_outcome(cls, outcome: CaseOutcome) -> dict[str, Any]:
        return {
            "case": cls.serialise_case(outcome.case),
            "output": cls.json_safe(outcome.output),
            "scores": [cls.serialise_score(score) for score in outcome.scores],
            "error": outcome.error,
            "run_index": outcome.run_index,
        }

    @staticmethod
    def summarise_runs(
        outcomes: list[CaseOutcome],
    ) -> dict[str, dict[str, float | int | None]]:
        """Mean, stdev and run count per metric, taking the case-mean within each run first."""
        per_run: dict[str, dict[int, list[float]]] = defaultdict(
            lambda: defaultdict(list)
        )
        for outcome in outcomes:
            for score in outcome.scores:
                per_run[score.name][outcome.run_index].append(score.value)

        summary: dict[str, dict[str, float | int | None]] = {}
        for name, runs in per_run.items():
            run_means = [mean(values) for values in runs.values()]
            # Averaging within a run before comparing runs means stdev reflects run-to-run variance
            summary[name] = {
                "mean": mean(run_means),
                "stdev": stdev(run_means) if len(run_means) > 1 else None,
                "n": len(run_means),
            }
        return summary

    @staticmethod
    def _comparable_items(output: Any) -> set:
        """Reduce a task output to a set of items (theme titles, or response/label pairs)."""
        if not isinstance(output, dict):
            return set()
        if "labels" in output:
            return {
                (response_id, label)
                for response_id, labels in output["labels"].items()
                for label in labels
            }
        return {
            str(theme.get("topic_label", theme.get("topic", ""))).strip().lower()
            for theme in output.get("themes", [])
        }

    @classmethod
    def output_consistency(cls, outputs: list[Any]) -> float | None:
        """Mean pairwise Jaccard overlap of a case's outputs across runs (1 = identical).

        Exact-match only: a reworded but equivalent theme counts as different, so this is
        a lower bound. None when fewer than two runs produced an output.
        """
        sets = [
            cls._comparable_items(output) for output in outputs if output is not None
        ]
        if len(sets) < 2:
            return None
        return mean(
            len(a & b) / len(a | b) if a | b else 1.0 for a, b in combinations(sets, 2)
        )

    @classmethod
    def consistency_by_case(cls, outcomes: list[CaseOutcome]) -> dict[str, float]:
        """output_consistency per case id, for cases with at least two successful runs."""
        outputs: dict[str, list[Any]] = defaultdict(list)
        for outcome in outcomes:
            if outcome.error is None:
                outputs[outcome.case.id].append(outcome.output)
        return {
            case_id: value
            for case_id, case_outputs in outputs.items()
            if (value := cls.output_consistency(case_outputs)) is not None
        }

    @classmethod
    def flatten_run_report(cls, report: RunReport) -> dict[str, Any]:
        results: dict[str, Any] = {}
        repeated = any(outcome.run_index > 0 for outcome in report.outcomes)

        for outcome in report.outcomes:
            # Repeats of one case share a key, so suffix the run to stop them overwriting
            key = cls.case_key(outcome.case)
            if repeated:
                key = f"{key}_r{outcome.run_index}"
            results[f"{key}_output"] = cls.json_safe(outcome.output)

            for score in outcome.scores:
                results[f"{key}_{score.name}"] = score.value

        if repeated:
            consistency = cls.consistency_by_case(report.outcomes)
            results["aggregate"] = {
                "metrics": cls.summarise_runs(report.outcomes),
                CONSISTENCY_METRIC: {
                    "mean": mean(consistency.values()) if consistency else None,
                    "by_case": consistency,
                },
            }

        if report.metrics is not None:
            results["metrics"] = cls.json_safe(report.metrics)

        return results

    @classmethod
    def build_results_payload(
        cls,
        component: str,
        dataset: str,
        report: RunReport,
        *,
        recorded_outcomes: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        outcomes = recorded_outcomes or [
            cls.serialise_outcome(outcome) for outcome in report.outcomes
        ]

        return {
            "component": component,
            "dataset": dataset,
            "results": cls.flatten_run_report(report),
            "outcomes": outcomes,
            "errors": {
                cls.case_key(outcome.case): outcome.error
                for outcome in report.outcomes
                if outcome.error is not None
            },
        }
