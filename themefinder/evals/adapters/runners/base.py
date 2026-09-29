"""RunnerPort — the port every eval-runner adapter implements.

settings.EvalRunSettings.engine is not yet wired to a runner-selection factory.
"""

from abc import ABC, abstractmethod
from collections import Counter
from typing import Any

from adapters.evaluators.base import EvaluatorPort
from eval_types import Case, ComponentConfig, RunReport


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
        selected = self._select_cases(config, cases)
        self._require_unique_case_ids(selected)
        return await self._run(config, selected, llm=llm)

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
    def _select_cases(config: ComponentConfig, cases: list[Case]) -> list[Case]:
        """Apply config.case_filter, shared by every concrete runner's _run."""
        return [
            case
            for case in cases
            if config.case_filter is None or config.case_filter(case)
        ]

    @staticmethod
    def _require_unique_case_ids(cases: list[Case]) -> None:
        """Fail fast: duplicate ids can misattribute results downstream (e.g. a
        runner's own by-id join, or ArtefactStorePort's by-id flattening)."""
        counts = Counter(case.id for case in cases)
        duplicates = [case_id for case_id, count in counts.items() if count > 1]
        if duplicates:
            raise ValueError(f"duplicate case ids: {duplicates}")
