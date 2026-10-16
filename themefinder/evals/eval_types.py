"""Domain types shared across the ports-and-adapters evaluation framework.

Deliberately free of any tool specific import — these are the
plain data shapes every port and runner operate on.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from adapters.evaluators.base import EvaluatorPort


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


@dataclass(frozen=True)
class RunMetrics:
    """Gateway and wall-clock metrics for one completed evaluation run.

    ``cost_usd`` and ``latency_seconds`` are summed from gateway response
    headers; latency is therefore not end-to-end run latency. The local
    ``processing_time_seconds`` covers case loading, evaluation and per-case
    artefact recording, but excludes final artefact finalisation. A value of
    ``None`` means that no compatible LLM calls were made, or token usage was
    not returned; it is never a stand-in zero.
    """

    cost_usd: float | None
    latency_seconds: float | None
    processing_time_seconds: float
    llm_call_count: int
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None


@dataclass
class CaseOutcome:
    case: Case
    output: Any
    scores: list[Score]
    error: str | None = None


@dataclass
class RunReport:
    outcomes: list[CaseOutcome]
    # Opaque escape hatch for a runner's own native report object, if it has one
    engine_report: Any | None = None
    metrics: RunMetrics | None = None


@dataclass
class ComponentConfig:
    component: str  # one of components.COMPONENT_NAMES
    task: Callable[[dict, Any], Awaitable[dict]]  # (case.inputs, llm) -> output dict
    evaluators: list["EvaluatorPort"]  # pre-built, with any judge llm already bound
    case_filter: Callable[[Case], bool] | None = None


class DatasetNotFoundError(Exception):
    """Raised when a configured dataset source can't provide the requested dataset."""
