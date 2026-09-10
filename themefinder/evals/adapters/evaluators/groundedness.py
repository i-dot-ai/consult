"""GroundednessEvaluator — how well generated themes are grounded in expected themes."""

from typing import Any

from eval_types import Case

from .common import ThemeComparisonJudgeEvaluator


class GroundednessEvaluator(ThemeComparisonJudgeEvaluator):
    metric_name = "groundedness"

    def _topic_lists(self, case: Case, output: Any) -> tuple[Any, Any]:
        generated_themes = output.get("themes", [])
        expected_themes = (case.expected_output or {}).get("themes", {})
        return generated_themes, expected_themes
