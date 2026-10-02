"""Tests for RunnerPort's shared llm validation and its two concrete adapters."""

from typing import Any

import pytest
from pydantic_evals.reporting import EvaluationReport

from adapters.evaluators.base import EvaluatorPort
from adapters.runners.base import RunnerPort
from adapters.runners.inline_sequential_runner import InlineSequentialRunner
from adapters.runners.pydantic_evals_runner import PydanticEvalsRunner
from conftest import make_case
from eval_types import Case, ComponentConfig, RunReport, Score


class _FakeEvaluator(EvaluatorPort):
    """Minimal EvaluatorPort returning one canned Score, for runner tests."""

    def __init__(self, score: Score):
        self._canned_score = score

    async def _score(self, case: Case, output: Any) -> list[Score]:
        """Ignore case/output entirely and return the canned score."""
        return [self._canned_score]


class _RunnerContractTests:
    """Shared behaviour every RunnerPort adapter must satisfy."""

    def make_runner(self) -> RunnerPort:
        """Build the concrete runner under test; overridden per adapter."""
        raise NotImplementedError

    def check_engine_report(
        self, report: RunReport, expected_cases: list[Case]
    ) -> None:
        """Assert engine_report looks right for this runner; differs per adapter."""
        raise NotImplementedError

    @staticmethod
    def _make_task(calls: list | None = None, raise_for_id: str | None = None):
        """Build a dummy ComponentConfig.task that records calls and can raise on demand."""

        async def task(inputs, llm):
            if calls is not None:
                calls.append((inputs, llm))
            if inputs.get("id") == raise_for_id:
                raise RuntimeError("boom")
            return {"echo": inputs["id"]}

        return task

    async def test_runs_task_and_evaluators_per_case_in_order(self):
        """Happy path: outcomes match cases by id and carry the evaluator's scores."""
        llm_sentinel = object()
        task_calls = []

        config = ComponentConfig(
            component="generation",
            task=self._make_task(calls=task_calls),
            evaluators=[_FakeEvaluator(Score("m1", 0.75, "note"))],
        )
        case1 = make_case(inputs={"id": "a"}, case_id="case-1")
        case2 = make_case(inputs={"id": "b"}, case_id="case-2")

        report = await self.make_runner().run(config, [case1, case2], llm=llm_sentinel)

        outcomes = {o.case.id: o for o in report.outcomes}
        assert outcomes["case-1"].output == {"echo": "a"}
        assert outcomes["case-1"].scores == [Score("m1", 0.75, "note")]
        assert outcomes["case-2"].output == {"echo": "b"}
        assert outcomes["case-2"].scores == [Score("m1", 0.75, "note")]
        assert task_calls == [({"id": "a"}, llm_sentinel), ({"id": "b"}, llm_sentinel)]
        self.check_engine_report(report, [case1, case2])

    async def test_raises_when_llm_missing(self):
        """run() fails fast when llm is None, before any case runs."""
        config = ComponentConfig(
            component="generation", task=self._make_task(), evaluators=[]
        )

        with pytest.raises(ValueError, match="llm is required"):
            await self.make_runner().run(
                config, [make_case(inputs={"id": "x"})], llm=None
            )

    async def test_raises_when_an_evaluator_is_not_an_evaluator_port(self):
        """run() fails fast when config.evaluators holds something other than an EvaluatorPort."""
        config = ComponentConfig(
            component="generation", task=self._make_task(), evaluators=[object()]
        )

        with pytest.raises(TypeError, match="must all be EvaluatorPort instances"):
            await self.make_runner().run(
                config, [make_case(inputs={"id": "x"})], llm="llm"
            )

    async def test_empty_cases_produces_no_outcomes(self):
        """Running against zero cases is a no-op, not an error."""
        config = ComponentConfig(
            component="generation", task=self._make_task(), evaluators=[]
        )

        report = await self.make_runner().run(config, [], llm="llm")

        assert report.outcomes == []

    async def test_raises_on_duplicate_case_ids(self):
        """run() fails fast on duplicate case ids, before any case runs."""
        config = ComponentConfig(
            component="generation", task=self._make_task(), evaluators=[]
        )
        case_a = make_case(inputs={"id": "a"}, case_id="dup")
        case_b = make_case(inputs={"id": "b"}, case_id="dup")

        with pytest.raises(ValueError, match="duplicate case ids"):
            await self.make_runner().run(config, [case_a, case_b], llm="llm")

    async def test_case_filter_excludes_case_before_task_runs(self):
        """A filtered-out case's task never runs and it's absent from outcomes."""
        task_calls = []

        config = ComponentConfig(
            component="generation",
            task=self._make_task(calls=task_calls),
            evaluators=[],
            case_filter=lambda case: case.id != "excluded",
        )
        kept = make_case(inputs={"id": "kept"}, case_id="kept")
        excluded = make_case(inputs={"id": "excluded"}, case_id="excluded")

        report = await self.make_runner().run(config, [kept, excluded], llm="llm")

        assert [o.case.id for o in report.outcomes] == ["kept"]
        assert task_calls == [(kept.inputs, "llm")]
        self.check_engine_report(report, [kept])

    async def test_task_error_becomes_case_outcome_error_without_aborting_run(self):
        """One case's task failure doesn't stop the other cases from succeeding."""
        config = ComponentConfig(
            component="generation",
            task=self._make_task(raise_for_id="bad"),
            evaluators=[],
        )
        good1 = make_case(inputs={"id": "good1"}, case_id="good1")
        bad = make_case(inputs={"id": "bad"}, case_id="bad")
        good2 = make_case(inputs={"id": "good2"}, case_id="good2")

        report = await self.make_runner().run(config, [good1, bad, good2], llm="llm")

        outcomes = {o.case.id: o for o in report.outcomes}
        assert outcomes["bad"].output is None
        assert outcomes["bad"].scores == []
        assert outcomes["bad"].error
        assert outcomes["good1"].output == {"echo": "good1"}
        assert outcomes["good1"].error is None
        assert outcomes["good2"].output == {"echo": "good2"}
        self.check_engine_report(report, [good1, bad, good2])


class TestInlineSequentialRunner(_RunnerContractTests):
    def make_runner(self) -> RunnerPort:
        """Build the runner under test."""
        return InlineSequentialRunner()

    def check_engine_report(
        self, report: RunReport, expected_cases: list[Case]
    ) -> None:
        """InlineSequentialRunner never has a native report."""
        assert report.engine_report is None


class TestPydanticEvalsRunner(_RunnerContractTests):
    """Uses the real pydantic_evals.Dataset.evaluate() engine, progress=False, no network."""

    def make_runner(self) -> RunnerPort:
        """Build the runner under test."""
        return PydanticEvalsRunner(progress=False)

    def check_engine_report(
        self, report: RunReport, expected_cases: list[Case]
    ) -> None:
        """engine_report is the real native EvaluationReport, covering every case."""
        assert isinstance(report.engine_report, EvaluationReport)
        seen = len(report.engine_report.cases) + len(report.engine_report.failures)
        assert seen == len(expected_cases)

    async def test_runs_correctly_under_concurrency(self):
        """Each case's own output is correctly attributed when max_concurrency > 1."""
        config = ComponentConfig(
            component="generation", task=self._make_task(), evaluators=[]
        )
        cases = [make_case(inputs={"id": f"c{i}"}, case_id=f"c{i}") for i in range(5)]

        report = await PydanticEvalsRunner(max_concurrency=2, progress=False).run(
            config, cases, llm="llm"
        )

        outcomes = {o.case.id: o.output for o in report.outcomes}
        assert outcomes == {f"c{i}": {"echo": f"c{i}"} for i in range(5)}

    def test_to_outcome_defensive_branch_when_case_is_in_neither_list(self):
        """The engine reporting neither success nor failure degrades to a clear error, not a crash."""
        outcome = PydanticEvalsRunner._to_outcome(
            make_case(case_id="missing"), report_case=None, failure=None
        )

        assert outcome.error == "missing from pydantic_evals report"
        assert outcome.output is None
        assert outcome.scores == []
