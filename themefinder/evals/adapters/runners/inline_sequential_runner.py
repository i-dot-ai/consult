"""InlineSequentialRunner — RunnerPort with no native engine."""

from typing import Any

from adapters.evaluators.base import EvaluatorPort
from eval_types import Case, CaseOutcome, ComponentConfig, RunReport, Score

from .base import RunnerPort


class InlineSequentialRunner(RunnerPort):
    """Runs each case's task and evaluators in-process, one case at a time."""

    async def _run(
        self,
        config: ComponentConfig,
        cases: list[Case],
        *,
        llm: Any,
    ) -> RunReport:
        """Run every selected case sequentially; engine_report is always None."""
        outcomes = [
            await self._run_case(case, config.task, config.evaluators, llm)
            for case in cases
        ]
        return RunReport(outcomes=outcomes, engine_report=None)

    async def _run_case(
        self,
        case: Case,
        task: Any,
        evaluators: list[EvaluatorPort],
        llm: Any,
    ) -> CaseOutcome:
        """Run the task then every evaluator for one case, catching task failures."""
        try:
            output = await task(case.inputs, llm)
        except Exception as e:
            return CaseOutcome(
                case=case, output=None, scores=[], error=f"{type(e).__name__}: {e}"
            )

        scores: list[Score] = []
        for evaluator in evaluators:
            # evaluator.evaluate() already has its own error boundary
            # (EvaluatorPort.evaluate), so no second layer is needed here.
            scores.extend(await evaluator.evaluate(case, output))
        return CaseOutcome(case=case, output=output, scores=scores, error=None)
