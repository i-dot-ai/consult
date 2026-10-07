"""Reusable test doubles for the evaluation framework."""

from __future__ import annotations

from contextlib import contextmanager
from types import SimpleNamespace
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


class FakeJudge:
    """Judge LLM test double that returns parsed content and records prompts."""

    def __init__(self, parsed: str = "{}"):
        self.parsed = parsed
        self.prompts: list[str] = []

    async def ainvoke(self, prompt: str) -> SimpleNamespace:
        self.prompts.append(prompt)
        return SimpleNamespace(parsed=self.parsed)


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


class FakeTrace:
    def __init__(self, trace_id: str):
        self.trace_id = trace_id
        self.updated_output = None
        self.trace_updates: list[dict] = []

    def update(self, *, output):
        self.updated_output = output

    def update_trace(self, **kwargs):
        self.trace_updates.append(kwargs)


class _FakeDatasetRunItemsApi:
    def __init__(self):
        self.create_calls = []
        self.error: Exception | None = None

    def create(self, *, request):
        self.create_calls.append(request)
        if self.error is not None:
            raise self.error


class _FakeLangfuseV3Api:
    def __init__(self):
        self.dataset_run_items = _FakeDatasetRunItemsApi()


class FakeLangfuseClient:
    def __init__(self):
        self.api = _FakeLangfuseV3Api()
        self.create_trace_id_calls = 0
        self.start_span_calls: list[dict] = []
        self.last_span_trace: FakeTrace | None = None
        self.span_exit_calls: list[tuple[type[Exception] | None, str | None]] = []
        self.scores: list[dict] = []
        self.flush_calls = 0
        self.raise_on_create_score: Exception | None = None

    def create_trace_id(self):
        self.create_trace_id_calls += 1
        return "generated-trace-id"

    @contextmanager
    def start_as_current_span(self, **kwargs):
        self.start_span_calls.append(kwargs)
        trace = FakeTrace(kwargs["trace_context"]["trace_id"])
        self.last_span_trace = trace
        try:
            yield trace
        except Exception as exc:
            self.span_exit_calls.append((type(exc), str(exc)))
            raise
        else:
            self.span_exit_calls.append((None, None))

    def create_score(self, **kwargs):
        if self.raise_on_create_score is not None:
            raise self.raise_on_create_score
        self.scores.append(kwargs)

    def flush(self):
        self.flush_calls += 1
