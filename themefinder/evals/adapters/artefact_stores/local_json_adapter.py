"""Local JSON artefact store implementation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from eval_types import CaseOutcome, RunReport

from .base import (
    ArtefactStorePort,
    build_results_payload,
    flatten_run_report,
    serialise_outcome,
)


class LocalJSONArtefactStore(ArtefactStorePort):
    def __init__(self, output_dir: str | Path | None = None):
        self.output_dir = (
            Path(output_dir)
            if output_dir is not None
            else Path(__file__).resolve().parents[2] / "local_eval_runs"
        )
        self._component: str | None = None
        self._dataset: str | None = None
        self._recorded_outcomes: list[dict[str, Any]] = []

    def start_run(self, component: str, dataset: str) -> None:
        self._component = component
        self._dataset = dataset
        self._recorded_outcomes = []

    def record_case(self, outcome: CaseOutcome) -> None:
        self._recorded_outcomes.append(serialise_outcome(outcome))

    def finish_run(
        self,
        report: RunReport,
        *,
        engine_report: Any | None = None,
    ) -> dict[str, Any]:
        del engine_report

        component = self._require_run_metadata("component")
        dataset = self._require_run_metadata("dataset")
        output_path = self.output_dir / component / dataset / "results.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        payload = build_results_payload(
            component,
            dataset,
            report,
            recorded_outcomes=self._recorded_outcomes,
        )
        output_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )

        return flatten_run_report(report)

    def _require_run_metadata(self, field: str) -> str:
        value = getattr(self, f"_{field}")
        if value is None:
            raise RuntimeError(
                f"start_run() must be called before using {type(self).__name__}"
            )
        return value
