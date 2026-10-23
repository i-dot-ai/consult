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

    @property
    def key(self) -> str:
        """Readable name in results: the question part when there is one, since a
        Langfuse item id is opaque, else the id."""
        question_part = self.metadata.get("question_part")
        return str(question_part) if question_part else self.id


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
    # Which repeat of the case this is, so repeats don't overwrite each other downstream
    run_index: int = 0


@dataclass
class RunReport:
    outcomes: list[CaseOutcome]
    # Opaque escape hatch for a runner's own native report object, if it has one
    engine_report: Any | None = None
    metrics: RunMetrics | None = None

    @property
    def repeated(self) -> bool:
        return any(outcome.run_index > 0 for outcome in self.outcomes)

    def outcome_key(self, outcome: CaseOutcome) -> str:
        """Repeats of one case share a case key, so suffix the run to stop them
        overwriting; a single run keeps the plain case key."""
        key = outcome.case.key
        return f"{key}_r{outcome.run_index}" if self.repeated else key


@dataclass
class ComponentConfig:
    component: str  # one of components.COMPONENT_NAMES
    task: Callable[[dict, Any], Awaitable[dict]]  # (case.inputs, llm) -> output dict
    evaluators: list["EvaluatorPort"]  # pre-built, with any judge llm already bound
    case_filter: Callable[[Case], bool] | None = None


class DatasetNotFoundError(Exception):
    """Raised when a configured dataset source can't provide the requested dataset."""
