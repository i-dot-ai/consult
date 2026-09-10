"""CoverageEvaluator — how well expected themes are covered by generated themes (recall direction)."""

from typing import Any

from eval_types import Case

from .common import ThemeComparisonJudgeEvaluator


class CoverageEvaluator(ThemeComparisonJudgeEvaluator):
    metric_name = "coverage"

    def _topic_lists(self, case: Case, output: Any) -> tuple[Any, Any]:
        generated_themes = output.get("themes", [])
        expected_themes = (case.expected_output or {}).get("themes", {})
        return expected_themes, generated_themes
