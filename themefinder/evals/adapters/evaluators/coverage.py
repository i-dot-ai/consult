"""CoverageEvaluator — how well expected themes are covered by generated themes (recall direction)."""

from typing import Any

from eval_types import Case
from prompts import generation_eval_prompt

from .common import ThemeComparisonJudgeEvaluator


class CoverageEvaluator(ThemeComparisonJudgeEvaluator):
    prompt_fn = staticmethod(generation_eval_prompt)
    metric_names = ("coverage",)
    shuffle = True
    decision_scored = True

    def _topic_lists(self, case: Case, output: Any) -> tuple[Any, Any]:
        generated_themes = output.get("themes", [])
        expected_themes = (case.expected_output or {}).get("themes", {})
        return expected_themes, generated_themes
