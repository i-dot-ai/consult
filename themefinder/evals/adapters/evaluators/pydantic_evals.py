"""PydanticEvalsEvaluator — run any pydantic-evals Evaluator behind EvaluatorPort.

Wraps a native pydantic-evals evaluator so it drops into any
`ComponentConfig.build_evaluators` list, translating its `EvaluatorOutput` into this
framework's `list[Score]`:

    PydanticEvalsEvaluator(Contains(value="expected substring"))
"""

from collections.abc import Mapping
from typing import Any

from eval_types import Case, Score
from pydantic_evals.evaluators import Evaluator, EvaluatorContext
from pydantic_evals.evaluators.evaluator import EvaluationReason
from pydantic_evals.otel import SpanTreeRecordingError

from .base import EvaluatorPort


class PydanticEvalsEvaluator(EvaluatorPort):
    def __init__(
        self, evaluator: Evaluator, metric_names: tuple[str, ...] | None = None
    ):
        """Wrap `evaluator` behind `EvaluatorPort`; single-output evaluators default
        their Score name from `get_default_evaluation_name()`, multi-output ones must
        declare `metric_names` rather than us reconstructing pydantic-evals' internal
        output-key naming (which would drift silently on upgrade).
        """
        self._evaluator = evaluator
        self.metric_names = metric_names or (evaluator.get_default_evaluation_name(),)

    @property
    def pydantic_evaluator(self) -> Evaluator:
        """The wrapped native pydantic-evals evaluator, for use by certain runners."""
        return self._evaluator

    def _build_context(self, case: Case, output: Any) -> EvaluatorContext:
        """Build an `EvaluatorContext` from a `Case` and task `output`.

        Timing/attributes/metrics/span-tree get inert placeholders, the
        extension point for a native runner to thread real observations is here (PRO-734).
        """
        return EvaluatorContext(
            name=case.id,
            inputs=case.inputs,
            metadata=case.metadata,
            expected_output=case.expected_output,
            output=output,
            duration=0.0,
            # `_span_tree` is a required kw-only dataclass field, so we must pass it
            _span_tree=SpanTreeRecordingError("span tree not recorded outside a run"),
            attributes={},
            metrics={},
        )

    async def _score(self, case: Case, output: Any) -> list[Score]:
        """Run the wrapped evaluator and project its `EvaluatorOutput` onto
        `metric_names`. Catches a KeyError for a mismatch of expected vs emitted metric names.
        """
        raw = await self._evaluator.evaluate_async(self._build_context(case, output))
        results = dict(raw) if isinstance(raw, Mapping) else {self.metric_names[0]: raw}
        try:
            # a size mismatch means undeclared extras; when sizes match, any key
            # mismatch forces a missing declared name in the projection (KeyError too)
            if len(results) != len(self.metric_names):
                raise KeyError
            return [self._to_score(name, results[name]) for name in self.metric_names]
        except KeyError as e:
            raise ValueError(
                f"{self._evaluator.get_serialization_name()} emitted metrics "
                f"{sorted(results)}, but metric_names declares "
                f"{sorted(self.metric_names)}. "
                f"Pass metric_names={tuple(results)} when wrapping it."
            ) from e

    def _to_score(self, name: str, value: Any) -> Score:
        """Convert a metric value (bare scalar or `EvaluationReason`) into a `Score`."""
        reason: str | None = None
        if isinstance(value, EvaluationReason):
            value, reason = value.value, value.reason

        # bool before int: isinstance(True, int) is True
        if isinstance(value, bool):
            return Score(name, 1.0 if value else 0.0, reason or "")
        if isinstance(value, (int, float)):
            return Score(name, float(value), reason or "")
        # non-numeric str label: keep it (and any reason) in the comment, no score
        comment = str(value) + (f" — {reason}" if reason else "")
        return Score(name, 0.0, comment)
