"""EvaluatorPort — the port every evaluator adapter implements.

Every concrete evaluator adapter must implement _score which takes
a case and the task output and returns a list of Score objects. This
is wrapped in evaluate which handles exceptions and logging.
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
        """Evaluate against the case and output and catch any errors.

        The concrete score functionality is implemented in _score().
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

        Always declared `async def` to cover all evaluator types.
        """

    @staticmethod
    def extract_theme_titles(themes: list[dict] | dict) -> list[str]:
        """Pull display titles out of a themes collection, in either shape a
        task output uses.

        TODO: the label-keyed dict (`{label: description}`) is the canonical
        theme shape going forward

        This will be fixed in PRO-734.
        """
        if isinstance(themes, list):
            return [t.get("topic_label", t.get("topic", "")) for t in themes]
        if isinstance(themes, dict):
            return list(themes.keys())
        return []
