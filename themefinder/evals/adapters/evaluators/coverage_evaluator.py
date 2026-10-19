"""CoverageEvaluator — how well expected themes are covered by generated themes (recall direction).

Sibling of GroundednessEvaluator, which scores the reverse direction.
"""

from .prompts import load_prompt_fn

from .llm_judge_evaluator import DecisionScoredComparisonJudge


class CoverageEvaluator(DecisionScoredComparisonJudge):
    prompt_fn = staticmethod(load_prompt_fn("generation"))
    metric_names = ("coverage",)
    threshold_label = "themes not captured"

    def __init__(self, *args, shuffle: bool = True, **kwargs):
        super().__init__(*args, **kwargs, shuffle=shuffle)
