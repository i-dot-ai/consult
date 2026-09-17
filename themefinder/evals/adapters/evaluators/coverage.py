"""CoverageEvaluator — how well expected themes are covered by generated themes (recall direction).

Sibling of GroundednessEvaluator, which scores the reverse direction.
"""

from prompts import generation_eval_prompt

from .llm_judge import DecisionScoredComparisonJudge


class CoverageEvaluator(DecisionScoredComparisonJudge):
    prompt_fn = staticmethod(generation_eval_prompt)
    metric_names = ("coverage",)
    threshold_label = "themes not captured"
    shuffle = True
