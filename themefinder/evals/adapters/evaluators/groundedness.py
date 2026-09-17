"""GroundednessEvaluator — how well generated themes are grounded in expected themes.

Sibling of CoverageEvaluator, which scores the reverse direction.
"""

from typing import Any

from prompts import generation_eval_prompt

from .llm_judge import DecisionScoredComparisonJudge


class GroundednessEvaluator(DecisionScoredComparisonJudge):
    prompt_fn = staticmethod(generation_eval_prompt)
    metric_names = ("groundedness",)
    threshold_label = "themes below threshold"
    shuffle = True

    def _topic_order(self, case_themes: Any, output_themes: Any) -> tuple[Any, Any]:
        """Score generated (output) themes against expected (case) themes, so
        output goes first."""
        return output_themes, case_themes
