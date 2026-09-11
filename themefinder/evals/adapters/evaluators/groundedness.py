"""GroundednessEvaluator — how well generated themes are grounded in expected themes.

Sibling of CoverageEvaluator (see that file for the reverse direction): both
drive `generation_eval_prompt`, an asymmetric topic-matching task — does
each theme in list A find a match in list B? Scoring "generated → expected"
and "expected → generated" are genuinely two separate LLM calls, not one
call that could be bundled and later split, which is why each direction
gets its own evaluator with a single metric rather than one evaluator
returning both. Contrast with CondensationQualityEvaluator/
RefinementQualityEvaluator, whose several metrics currently *do* share one
call — see those files for why.
"""

from typing import Any

from prompts import generation_eval_prompt

from .common import ThemeComparisonJudgeEvaluator


class GroundednessEvaluator(ThemeComparisonJudgeEvaluator):
    prompt_fn = staticmethod(generation_eval_prompt)
    metric_names = ("groundedness",)
    shuffle = True
    decision_scored = True

    def _topic_order(self, case_themes: Any, output_themes: Any) -> tuple[Any, Any]:
        return output_themes, case_themes
