"""RefinementQualityEvaluator — four-dimension quality assessment of theme refinement.

Compares `output["themes"]` (refined) against `case.inputs["themes"]` (the
pre-refinement themes) — not `case.expected_output`, for the same reason as
CondensationQualityEvaluator: refinement has no ground truth to compare
against, only a before/after pair. Also a two-theme-list comparison, so it
inherits `ThemeComparisonJudgeEvaluator` the same way condensation does:
`shuffle`/`decision_scored` stay `False`, extracting four named numeric keys
directly via `ThemeComparisonJudgeEvaluator`'s shared `_build_scores`.

NOTE: this one LLM call scores four metrics (information_retention,
response_references, distinctiveness, fluency) together, same as today's
evaluators.py — one combined prompt/response, one shared calibration example.
Splitting this into one prompt per metric is deliberately deferred to a later
issue reviewing the LLM-as-judge prompts themselves; see prompts.py's
refinement_eval_prompt.
"""

from typing import Any

from eval_types import Case
from prompts import refinement_eval_prompt

from .common import ThemeComparisonJudgeEvaluator


class RefinementQualityEvaluator(ThemeComparisonJudgeEvaluator):
    prompt_fn = staticmethod(refinement_eval_prompt)
    first_kwarg = "original_topics"
    second_kwarg = "new_topics"
    metric_names = (
        "information_retention",
        "response_references",
        "distinctiveness",
        "fluency",
    )

    def _topic_lists(self, case: Case, output: Any) -> tuple[Any, Any]:
        original_themes = case.inputs.get("themes", [])
        refined_themes = output.get("themes", [])
        return original_themes, refined_themes
