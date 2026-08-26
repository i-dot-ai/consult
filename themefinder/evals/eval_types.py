"""Domain types shared across the ports-and-adapters evaluation framework.

Deliberately free of any `langfuse` or `pydantic_evals` import — these are the
plain data shapes every port (`DatasetPort`, `EvaluatorPort`, `EvalRunnerPort`,
`ArtefactStorePort`) and `stage_runner.py` operate on.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Case:
    id: str
    inputs: dict[str, Any]
    expected_output: dict[str, Any] | None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Score:
    name: str
    value: float
    comment: str = ""


@dataclass
class CaseOutcome:
    case: Case
    output: Any
    scores: list[Score]
    error: str | None = None


@dataclass
class RunReport:
    outcomes: list[CaseOutcome]
    # Opaque escape hatch for a runner's own native report object, if it has
    # one (e.g. pydantic_evals.reporting.EvaluationReport). None for runners
    # that don't have a native report (InlineSequentialRunner and friends).
    # Untyped deliberately: eval_types.py never imports pydantic_evals.
    engine_report: Any | None = None


@dataclass
class StageConfig:
    stage: str  # one of datasets.VALID_STAGES
    task: Callable[[dict, Any], Awaitable[dict]]  # (case.inputs, llm) -> output dict
    build_evaluators: Callable[[Any], list[Any]]  # (judge_llm) -> list[EvaluatorPort]
    case_filter: Callable[[Case], bool] | None = None


class DatasetNotFoundError(Exception):
    """Raised when a configured dataset source can't provide the requested dataset."""
