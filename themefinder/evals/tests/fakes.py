"""Reusable test doubles for the evaluation orchestration ports."""

from __future__ import annotations

from typing import Any

from adapters.artefact_stores.base import ArtefactStorePort, flatten_run_report
from adapters.datasets.base import DatasetPort
from adapters.evaluators.base import EvaluatorPort
from adapters.runners.base import RunnerPort
from datasets import DatasetConfig
from eval_types import Case, CaseOutcome, ComponentConfig, RunReport, Score


class FakeDatasetPort(DatasetPort):
    def __init__(
        self,
        cases: list[Case],
        *,
        events: list[str] | None = None,
        error: Exception | None = None,
    ):
        self.cases = cases
        self.events = events
        self.error = error
        self.loaded_configs: list[DatasetConfig] = []

    def load_cases(self, config: DatasetConfig) -> list[Case]:
        if self.events is not None:
            self.events.append("load_cases")
        self.loaded_configs.append(config)
        if self.error is not None:
            raise self.error
        return self.cases


class FakeEvaluatorPort(EvaluatorPort):
    def __init__(self, scores: list[Score]):
        self.scores = scores
        self.calls: list[tuple[Case, Any]] = []

    async def _score(self, case: Case, output: Any) -> list[Score]:
        self.calls.append((case, output))
        return self.scores


class FakeRunnerPort(RunnerPort):
    def __init__(
        self,
        report: RunReport,
        *,
        events: list[str] | None = None,
        error: Exception | None = None,
    ):
        self.report = report
        self.events = events
        self.error = error
        self.calls: list[tuple[ComponentConfig, list[Case], Any]] = []

    async def _run(
        self,
        config: ComponentConfig,
        cases: list[Case],
        *,
        llm: Any,
    ) -> RunReport:
        if self.events is not None:
            self.events.append("run")
        self.calls.append((config, cases, llm))
        if self.error is not None:
            raise self.error
        return self.report


class FakeArtefactStore(ArtefactStorePort):
    def __init__(
        self,
        *,
        events: list[str] | None = None,
        result: dict[str, Any] | None = None,
        record_error: Exception | None = None,
    ):
        self.events = events
        self.result = result
        self.record_error = record_error
        self.started_with: tuple[str, str] | None = None
        self.recorded: list[CaseOutcome] = []
        self.finished_with: tuple[RunReport, Any | None] | None = None

    def start_run(self, component: str, dataset: str) -> None:
        if self.events is not None:
            self.events.append("start_run")
        self.started_with = (component, dataset)

    def record_case(self, outcome: CaseOutcome) -> None:
        if self.events is not None:
            self.events.append(f"record_case:{outcome.case.id}")
        if self.record_error is not None:
            raise self.record_error
        self.recorded.append(outcome)

    def finish_run(
        self,
        report: RunReport,
        *,
        engine_report: Any | None = None,
    ) -> dict[str, Any]:
        if self.events is not None:
            self.events.append("finish_run")
        self.finished_with = (report, engine_report)
        return self.result if self.result is not None else flatten_run_report(report)
