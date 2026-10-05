"""RunnerPort — the port every eval-runner adapter implements.

config.resolve_backends() selects the runner using settings.EvalRunSettings.engine.
"""

from abc import ABC, abstractmethod
from collections import Counter
from typing import Any

from adapters.evaluators.base import EvaluatorPort
from eval_types import Case, CaseOutcome, ComponentConfig, RunReport


class RunnerPort(ABC):
    async def run(
        self,
        config: ComponentConfig,
        cases: list[Case],
        *,
        llm: Any,
    ) -> RunReport:
        """Validate llm/config.evaluators, apply case_filter, then delegate to the subclass's _run."""
        if llm is None:
            raise ValueError("llm is required")
        for evaluator in config.evaluators:
            if not isinstance(evaluator, EvaluatorPort):
                raise TypeError(
                    "config.evaluators must all be EvaluatorPort instances, got "
                    f"{type(evaluator).__name__}. Wrap a native pydantic_evals evaluator "
                    "in PydanticEvalsEvaluator(...) first."
                )
        selected, rejected = self._select_cases(config, cases)
        self._require_unique_case_ids(selected)
        report = await self._run(config, selected, llm=llm)
        report.outcomes.extend(rejected)
        return report

    @abstractmethod
    async def _run(
        self,
        config: ComponentConfig,
        cases: list[Case],
        *,
        llm: Any,
    ) -> RunReport:
        """Run config.task and score with config.evaluators over the already-filtered cases."""

    @staticmethod
    def _select_cases(
        config: ComponentConfig, cases: list[Case]
    ) -> tuple[list[Case], list[CaseOutcome]]:
        """Apply config.case_filter, then split off cases with an empty id.

        Empty ids can't be joined back reliably by runners or artefact stores, so
        those cases are never run; they come back as unscored error outcomes.
        """
        filtered = [
            case
            for case in cases
            if config.case_filter is None or config.case_filter(case)
        ]
        selected = [case for case in filtered if case.id]
        rejected = [
            CaseOutcome(case=case, output=None, scores=[], error="empty case id")
            for case in filtered
            if not case.id
        ]
        return selected, rejected

    @staticmethod
    def _require_unique_case_ids(cases: list[Case]) -> None:
        """Fail fast: duplicate ids can misattribute results downstream (e.g. a
        runner's own by-id join, or ArtefactStorePort's by-id flattening)."""
        counts = Counter(case.id for case in cases)
        duplicates = [case_id for case_id, count in counts.items() if count > 1]
        if duplicates:
            raise ValueError(f"duplicate case ids: {duplicates}")
