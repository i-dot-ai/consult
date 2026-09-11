"""EvaluatorPort — the port every evaluator adapter implements.

Deliberately narrow: one abstract method, `_score()`, scoring a single
case's task output. `evaluate()` itself is concrete — it wraps `_score()`
in the error boundary every adapter needs (log the failure, fall back to a
zero Score per name in `metric_names`) so subclasses don't each reimplement
that try/except. `EvalRunnerPort` implementations invoke `evaluate()` once
per case, per evaluator, and stay agnostic to which kind of evaluator (LLM
judge, deterministic metric, embedding-based) they're driving.
`extract_theme_titles` below is a second shared helper, unrelated to error
handling — subclasses inherit it but never override it.

Dataset-level aggregation (mean/std per metric across a run) deliberately
lives elsewhere, not on this port — see the "Deliberately out of scope"
section of the PRO-729 plan. An evaluator only ever sees one case per call;
aggregating here would mean accumulating state across concurrent `evaluate()`
calls, which a stateless per-case scorer avoids entirely. That's a
RunReport/EvalRunnerPort-level concern instead.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

from eval_types import Case, Score

logger = logging.getLogger(__name__)


class EvaluatorPort(ABC):
    #: Score names this evaluator produces. Every concrete subclass sets
    #: this — used by the error-path fallback below to return one zero
    #: Score per metric instead of just swallowing the failure silently.
    metric_names: tuple[str, ...] = ()

    async def evaluate(self, case: Case, output: Any) -> list[Score]:
        """Score `output` (the task's result for `case`) and return one or more Scores.

        Concrete — wraps `_score()` in the shared error boundary: any
        exception is logged and turned into a zero Score per name in
        `metric_names`, so one evaluator's judge timeout or malformed
        response degrades that metric to 0 rather than failing the whole run.
        """
        try:
            return await self._score(case, output)
        except Exception as e:
            logger.error(f"{type(self).__name__} evaluation failed: {e}")
            return [Score(name, 0.0, f"Error: {e}") for name in self.metric_names]

    @abstractmethod
    async def _score(self, case: Case, output: Any) -> list[Score]:
        """Do the actual scoring of `output` for `case` — no error handling
        needed here, `evaluate()` above wraps this in the shared try/except.

        Always declared `async def`, even for evaluators whose body never
        awaits anything (deterministic or embedding-based evaluators) —
        callers always `await evaluate(...)` uniformly.
        """

    @staticmethod
    def extract_theme_titles(themes: list[dict] | dict) -> list[str]:
        """Pull display titles out of a themes collection, in either shape a
        task output uses: a list of dicts keyed by `topic_label`/`topic`, or a
        dict keyed by label. Shared by TitleSpecificityEvaluator and
        RedundancyEvaluator, which both only care about the title strings.
        """
        if isinstance(themes, list):
            return [t.get("topic_label", t.get("topic", "")) for t in themes]
        if isinstance(themes, dict):
            return list(themes.keys())
        return []
