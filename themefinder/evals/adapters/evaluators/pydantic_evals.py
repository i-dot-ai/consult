"""PydanticEvalsEvaluator — run any pydantic-evals Evaluator behind EvaluatorPort.

Wraps a native pydantic-evals evaluator so it drops into any
`ComponentConfig.build_evaluators` list, translating its `EvaluatorOutput` into this
framework's `list[Score]`. Point an `LLMJudge` at this repo's LLM gateway by building
its model with `gateway_judge_model()`:

    PydanticEvalsEvaluator(LLMJudge(rubric="...", model=gateway_judge_model("claude-sonnet-4"), score=OutputConfig()))
"""

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from eval_types import Case, Score
from pydantic_evals.evaluators import Evaluator, EvaluatorContext, LLMJudge
from pydantic_evals.evaluators.evaluator import EvaluationReason
from pydantic_evals.otel import SpanTreeRecordingError

from .base import EvaluatorPort

if TYPE_CHECKING:
    from pydantic_ai.models.openai import OpenAIChatModel


class PydanticEvalsEvaluator(EvaluatorPort):
    def __init__(self, evaluator: Evaluator):
        """Wrap a pydantic-evals `evaluator` behind `EvaluatorPort`."""
        self._evaluator = evaluator
        self.metric_names = self._derive_metric_names(evaluator)

    @staticmethod
    def _derive_metric_names(evaluator: Evaluator) -> tuple[str, ...]:
        """Predict the Score names `evaluator` will emit, so callers needn't declare them.

        `LLMJudge` names are derived exactly from its `score`/`assertion` config (both set
        → `<name>_score` and `<name>_pass`); every other evaluator is assumed
        single-output, named by `get_default_evaluation_name()`.
        """
        if isinstance(evaluator, LLMJudge):
            base = evaluator.get_default_evaluation_name()
            m_types = ["score", "assertion"]
            active = [m for m in m_types if getattr(evaluator, m) is not False]
            include_both = len(active) == 2
            # pydantic-evals suffixes the assertion result `_pass`, not `_assertion`
            suffixes = {"score": "_score", "assertion": "_pass"}
            names = []
            for m_type in active:
                config = getattr(evaluator, m_type)
                default = f"{base}{suffixes[m_type]}" if include_both else base
                names.append(config.get("evaluation_name") or default)
            return tuple(names)

        return (evaluator.get_default_evaluation_name(),)

    def _build_context(self, case: Case, output: Any) -> EvaluatorContext:
        """Build a pydantic-evals `EvaluatorContext` from a `Case` and task `output`.

        Four fields the framework doesn't model (timing, attributes, metrics, span tree)
        get inert placeholders, since pydantic-evals' own `Dataset.evaluate()` loop isn't
        driving us; the `_span_tree` placeholder only raises if an evaluator reads it. Our
        intended targets (`LLMJudge` and the like) read none of these — they're a task's
        run-time observations, only populated when a pydantic-evals runner executes the
        task under OTEL. This is the extension point for that: a future pydantic-evals
        runner could thread real observations in here (see PRO-734).
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
        """Run the wrapped evaluator and project its output onto `metric_names`.

        A scalar/reason return is the single derived metric; a mapping is looked up by
        name, with any name the evaluator didn't return degrading to a zero Score.
        """
        raw = await self._evaluator.evaluate_async(self._build_context(case, output))
        results = raw if isinstance(raw, Mapping) else {self.metric_names[0]: raw}
        return [
            self._to_score(name, results[name])
            if name in results
            else Score(name, 0.0, "Not returned by evaluator")
            for name in self.metric_names
        ]

    def _to_score(self, name: str, value: Any) -> Score:
        """Convert one derived metric's value (a bare scalar or `EvaluationReason`) into a
        `Score`. `bool` is checked before `int` because `isinstance(True, int)` is True.
        """
        reason: str | None = None
        if isinstance(value, EvaluationReason):
            value, reason = value.value, value.reason

        if isinstance(value, bool):
            return Score(name, 1.0 if value else 0.0, reason or "")
        if isinstance(value, (int, float)):
            return Score(name, float(value), reason or "")
        # str label: no numeric score — record it (and any reason) in the comment.
        comment = str(value) + (f" — {reason}" if reason else "")
        return Score(name, 0.0, comment)


def gateway_judge_model(name: str) -> "OpenAIChatModel":
    """Build a pydantic-ai `OpenAIChatModel` for gateway model-group `name`, for an
    `LLMJudge(model=)`, pointed at the gateway via the shared `gateway_credentials()`.
    pydantic-ai is imported lazily so wrapping non-LLM evaluators never pulls it in.
    """
    from pydantic_ai.models.openai import OpenAIChatModel
    from pydantic_ai.providers.openai import OpenAIProvider
    from utils.gateway import gateway_credentials

    base_url, api_key = gateway_credentials()
    return OpenAIChatModel(
        name, provider=OpenAIProvider(base_url=base_url, api_key=api_key)
    )
