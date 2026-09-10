"""CondensationQualityEvaluator — compression quality + information retention when
condensing a large theme set into a smaller one.

Compares `output["themes"]` (condensed) against `case.inputs["themes"]` (the
pre-condensation themes) — not `case.expected_output`, which is `None` for
condensation cases (no ground truth; see `datasets.py::load_local_condensation_data`).
This is a two-theme-list comparison like groundedness/coverage, so it
inherits `ThemeComparisonJudgeEvaluator`'s prompt-building — but doesn't
shuffle (`shuffle` stays `False`) and isn't ternary decision-scored
(`decision_scored` stays `False`): it extracts two named numeric keys
directly via its own `_build_scores`.

NOTE: this one LLM call scores two metrics (compression_quality,
information_retention) together, same as today's evaluators.py — one combined
prompt/response, one shared calibration example. Splitting this into one
prompt per metric is deliberately deferred to a later issue reviewing the
LLM-as-judge prompts themselves; see prompts.py's condensation_eval_prompt.
"""

from typing import Any

from eval_types import Case, Score
from prompts import condensation_eval_prompt

from .common import ThemeComparisonJudgeEvaluator


class CondensationQualityEvaluator(ThemeComparisonJudgeEvaluator):
    prompt_fn = staticmethod(condensation_eval_prompt)
    first_kwarg = "original_topics"
    second_kwarg = "condensed_topics"
    metric_names = ("compression_quality", "information_retention")

    def _topic_lists(self, case: Case, output: Any) -> tuple[Any, Any]:
        original_themes = case.inputs.get("themes", [])
        condensed_themes = output.get("themes", [])
        return original_themes, condensed_themes

    def _build_scores(self, parsed: dict) -> list[Score]:
        return [
            Score(
                metric,
                round(float(parsed.get(metric, 0)), 2),
                parsed.get(f"{metric}_reasoning", ""),
            )
            for metric in self.metric_names
        ]
