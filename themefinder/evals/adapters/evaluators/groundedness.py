"""GroundednessEvaluator — how well generated themes are grounded in expected themes."""

from typing import Any

from eval_types import Case
from prompts import generation_eval_prompt

from .common import ThemeComparisonJudgeEvaluator


class GroundednessEvaluator(ThemeComparisonJudgeEvaluator):
    prompt_fn = staticmethod(generation_eval_prompt)
    metric_names = ("groundedness",)
    shuffle = True
    decision_scored = True

    def _topic_lists(self, case: Case, output: Any) -> tuple[Any, Any]:
        generated_themes = output.get("themes", [])
        expected_themes = (case.expected_output or {}).get("themes", {})
        return generated_themes, expected_themes
