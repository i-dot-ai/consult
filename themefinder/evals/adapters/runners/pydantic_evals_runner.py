"""PydanticEvalsRunner — RunnerPort backed by the native pydantic_evals.Dataset engine."""

from collections import defaultdict
from dataclasses import dataclass, replace
from typing import Any

from pydantic_evals import Case as NativeCase
from pydantic_evals import Dataset
from pydantic_evals.evaluators import Evaluator, EvaluatorContext
from pydantic_evals.evaluators.evaluator import EvaluationReason
from pydantic_evals.reporting import EvaluationReport, ReportCase, ReportCaseFailure

from adapters.evaluators.base import EvaluatorPort
from adapters.evaluators.pydantic_evals_evaluator import PydanticEvalsEvaluator
from eval_types import Case, CaseOutcome, ComponentConfig, RunReport, Score

from .base import RunnerPort


@dataclass
class _EvaluatorPortAsNativeEvaluator(Evaluator):
    """Wraps one EvaluatorPort as a native Evaluator so it can run inside a Dataset."""

    port: EvaluatorPort

    def get_default_evaluation_name(self) -> str:
        """Use the wrapped port's name as the default evaluation name."""
        return self.port.name

    def evaluate(self, ctx: EvaluatorContext) -> dict[str, EvaluationReason]:
        """Never called directly — pydantic_evals always calls evaluate_async below."""
        raise NotImplementedError

    async def evaluate_async(
        self, ctx: EvaluatorContext
    ) -> dict[str, EvaluationReason]:
        """Delegate to the port and translate scores back.

        A PydanticEvalsEvaluator gets the real native ctx (real tracing); any other port
        gets a Case rebuilt from ctx. Both go through the port's own error handling.
        """
        if isinstance(self.port, PydanticEvalsEvaluator):
            scores = await self.port.evaluate_in_context(ctx)
        else:
            case = Case(
                id=ctx.name,
                inputs=ctx.inputs,
                expected_output=ctx.expected_output,
                metadata=ctx.metadata or {},
            )
            scores = await self.port.evaluate(case, ctx.output)
        return {
            score.name: EvaluationReason(
                value=score.value, reason=score.comment or None
            )
            for score in scores
        }


class PydanticEvalsRunner(RunnerPort):
    """Runs cases through the native pydantic_evals engine and reports back via RunReport."""

    def __init__(
        self,
        *,
        max_concurrency: int | None = None,
        progress: bool = True,
        repeat: int = 1,
    ):
        super().__init__(repeat=repeat)
        self._max_concurrency = max_concurrency
        self._progress = progress

    async def _run(
        self,
        config: ComponentConfig,
        cases: list[Case],
        *,
        llm: Any,
    ) -> RunReport:
        """Build a native Dataset from the selected cases and evaluators, then run it."""
        native_evaluators = tuple(
            _EvaluatorPortAsNativeEvaluator(port=evaluator)
            for evaluator in config.evaluators
        )
        dataset = Dataset(
            name=config.component,
            cases=[self._to_native_case(case) for case in cases],
            evaluators=native_evaluators,
        )

        async def task(inputs: dict) -> dict:
            return await config.task(inputs, llm)

        native_report = await dataset.evaluate(
            task,
            name=config.component,
            max_concurrency=self._max_concurrency,
            progress=self._progress,
            repeat=self.repeat,
        )
        return self._to_run_report(native_report, cases, self.repeat)

    @staticmethod
    def _to_native_case(case: Case) -> NativeCase:
        """Convert our Case into a native pydantic_evals Case, keyed by id."""
        return NativeCase(
            name=case.id,
            inputs=case.inputs,
            metadata=case.metadata or None,
            expected_output=case.expected_output,
        )

    @staticmethod
    def _to_run_report(
        native_report: EvaluationReport, cases: list[Case], repeat: int = 1
    ) -> RunReport:
        """Translate a native EvaluationReport back into our RunReport, keeping it as engine_report.

        With repeat > 1 pydantic_evals renames each run "<id> [i/N]" and keeps the id in
        source_case_name, so group on that to get back to one set of runs per case.
        """
        report_cases: dict[str, list[ReportCase]] = defaultdict(list)
        for report_case in native_report.cases:
            report_cases[report_case.source_case_name or report_case.name].append(
                report_case
            )
        failures: dict[str, list[ReportCaseFailure]] = defaultdict(list)
        for failure in native_report.failures:
            failures[failure.source_case_name or failure.name].append(failure)

        outcomes = []
        for case in cases:
            # Repeats are exchangeable, so run_index is just position within the group.
            # A run missing from the report is filled in as an error so every case has
            # exactly `repeat` outcomes.
            case_runs = [
                *((run, None) for run in report_cases.get(case.id, [])),
                *((None, failure) for failure in failures.get(case.id, [])),
            ]
            case_runs += [(None, None)] * (repeat - len(case_runs))
            outcomes.extend(
                replace(
                    PydanticEvalsRunner._to_outcome(case, report_case, failure),
                    run_index=run_index,
                )
                for run_index, (report_case, failure) in enumerate(case_runs)
            )
        return RunReport(outcomes=outcomes, engine_report=native_report)

    @staticmethod
    def _to_outcome(
        case: Case,
        report_case: ReportCase | None,
        failure: ReportCaseFailure | None,
    ) -> CaseOutcome:
        """Build one CaseOutcome from its matching native report case or failure."""
        if report_case is not None:
            scores = [
                Score(name, float(result.value), result.reason or "")
                for name, result in {
                    **report_case.scores,
                    **report_case.assertions,
                }.items()
            ]
            return CaseOutcome(
                case=case, output=report_case.output, scores=scores, error=None
            )
        if failure is not None:
            return CaseOutcome(
                case=case, output=None, scores=[], error=failure.error_message
            )
        return CaseOutcome(
            case=case,
            output=None,
            scores=[],
            error="missing from pydantic_evals report",
        )
