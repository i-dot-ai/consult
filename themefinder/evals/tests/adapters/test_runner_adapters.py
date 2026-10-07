"""Tests for RunnerPort's shared llm validation and its two concrete adapters."""

import pytest
from pydantic_evals.reporting import EvaluationReport

from adapters.runners.base import RunnerPort
from adapters.runners.inline_sequential_runner import InlineSequentialRunner
from adapters.runners.pydantic_evals_runner import PydanticEvalsRunner
from conftest import make_case
from eval_types import Case, CaseOutcome, ComponentConfig, RunReport, Score
from fakes import FakeEvaluatorPort


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
            evaluators=[FakeEvaluatorPort([Score("m1", 0.75, "note")])],
        )
        case1 = make_case(inputs={"id": "a"}, case_id="case-1")
        case2 = make_case(inputs={"id": "b"}, case_id="case-2")

        report = await self.make_runner().run(config, [case1, case2], llm=llm_sentinel)

        outcomes = {o.case.id: o for o in report.outcomes}
        assert outcomes["case-1"].output == {"echo": "a"}, "case-1 output misattributed"
        assert outcomes["case-1"].scores == [Score("m1", 0.75, "note")], (
            "case-1 should carry the evaluator's score"
        )
        assert outcomes["case-2"].output == {"echo": "b"}, "case-2 output misattributed"
        assert outcomes["case-2"].scores == [Score("m1", 0.75, "note")], (
            "case-2 should carry the evaluator's score"
        )
        assert task_calls == [
            ({"id": "a"}, llm_sentinel),
            ({"id": "b"}, llm_sentinel),
        ], "task should run once per case, in order, with the bound llm"
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

        assert report.outcomes == [], "zero cases should produce zero outcomes"

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

        assert [o.case.id for o in report.outcomes] == ["kept"], (
            "only the unfiltered case should appear in outcomes"
        )
        assert task_calls == [(kept.inputs, "llm")], (
            "task should not run for the filtered-out case"
        )
        self.check_engine_report(report, [kept])

    async def test_empty_case_ids_are_not_run_and_return_error_outcomes(self):
        """Empty-id cases skip the task and come back unscored with an error, even when repeated."""
        blank_id = ""
        task_calls = []
        config = ComponentConfig(
            component="generation",
            task=self._make_task(calls=task_calls),
            evaluators=[FakeEvaluatorPort([Score("m", 1.0)])],
        )
        good = make_case(inputs={"id": "good"}, case_id="good")
        blank1 = make_case(inputs={"id": "b1"}, case_id=blank_id)
        blank2 = make_case(inputs={"id": "b2"}, case_id=blank_id)

        report = await self.make_runner().run(config, [blank1, good, blank2], llm="llm")

        assert task_calls == [(good.inputs, "llm")], (
            "task ran for a case with an empty id"
        )
        assert len(report.outcomes) == 3, "expected one outcome per non-filtered case"
        blanks = [o for o in report.outcomes if o.case.id == blank_id]
        assert blanks == [
            CaseOutcome(case=blank, output=None, scores=[], error="empty case id")
            for blank in (blank1, blank2)
        ], "empty-id cases should be unscored outcomes with error 'empty case id'"
        (ok,) = [o for o in report.outcomes if o.case.id == "good"]
        assert ok.error is None, f"valid case should not have errored, got {ok.error}"
        self.check_engine_report(report, [good])

    async def test_case_filter_runs_before_empty_id_check(self):
        """An empty-id case the filter excludes is dropped, not reported as an error."""
        config = ComponentConfig(
            component="generation",
            task=self._make_task(),
            evaluators=[],
            case_filter=lambda case: case.id != "",
        )
        report = await self.make_runner().run(
            config, [make_case(inputs={"id": "x"}, case_id="")], llm="llm"
        )

        assert report.outcomes == [], (
            "filtered-out empty-id case should not be reported"
        )

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
        assert outcomes["bad"].output is None, "failed case should have no output"
        assert outcomes["bad"].scores == [], "failed case should not be scored"
        assert outcomes["bad"].error, "failed case should record an error message"
        assert outcomes["good1"].output == {"echo": "good1"}, (
            "good1 should still succeed"
        )
        assert outcomes["good1"].error is None, "good1 should not have errored"
        assert outcomes["good2"].output == {"echo": "good2"}, (
            "good2 should still succeed"
        )
        self.check_engine_report(report, [good1, bad, good2])


class TestInlineSequentialRunner(_RunnerContractTests):
    def make_runner(self) -> RunnerPort:
        """Build the runner under test."""
        return InlineSequentialRunner()

    def check_engine_report(
        self, report: RunReport, expected_cases: list[Case]
    ) -> None:
        """InlineSequentialRunner never has a native report."""
        assert report.engine_report is None, "inline runner has no native report"


class TestPydanticEvalsRunner(_RunnerContractTests):
    """Uses the real pydantic_evals.Dataset.evaluate() engine, progress=False, no network."""

    def make_runner(self) -> RunnerPort:
        """Build the runner under test."""
        return PydanticEvalsRunner(progress=False)

    def check_engine_report(
        self, report: RunReport, expected_cases: list[Case]
    ) -> None:
        """engine_report is the real native EvaluationReport, covering every case."""
        assert isinstance(report.engine_report, EvaluationReport), (
            "engine_report should be the native EvaluationReport"
        )
        seen = len(report.engine_report.cases) + len(report.engine_report.failures)
        assert seen == len(expected_cases), (
            "native report should cover every case that was run"
        )

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
        assert outcomes == {f"c{i}": {"echo": f"c{i}"} for i in range(5)}, (
            "each case's output should be attributed to its own id under concurrency"
        )

    def test_to_outcome_defensive_branch_when_case_is_in_neither_list(self):
        """The engine reporting neither success nor failure degrades to a clear error, not a crash."""
        case = make_case(case_id="missing")

        outcome = PydanticEvalsRunner._to_outcome(case, report_case=None, failure=None)

        assert outcome == CaseOutcome(
            case, None, [], "missing from pydantic_evals report"
        ), "missing case should be an unscored error outcome"
