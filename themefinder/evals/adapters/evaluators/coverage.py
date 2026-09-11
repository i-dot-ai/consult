"""CoverageEvaluator — how well expected themes are covered by generated themes (recall direction).

Sibling of GroundednessEvaluator (see that file for the reverse direction
and the general note on why groundedness/coverage split into two
single-metric evaluators while condensation/refinement don't).
"""

from prompts import generation_eval_prompt

from .common import ThemeComparisonJudgeEvaluator


class CoverageEvaluator(ThemeComparisonJudgeEvaluator):
    prompt_fn = staticmethod(generation_eval_prompt)
    metric_names = ("coverage",)
    shuffle = True
    decision_scored = True
