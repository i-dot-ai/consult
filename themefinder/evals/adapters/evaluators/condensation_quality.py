"""CondensationQualityEvaluator — compression quality + information retention when
condensing a large theme set into a smaller one.

Compares `output["themes"]` (condensed) against `case.inputs["themes"]` (the
pre-condensation themes) — not `case.expected_output`, which is `None` for
condensation cases (no ground truth; see `datasets.py::load_local_condensation_data`).
This is a two-theme-list comparison like groundedness/coverage, so it
inherits `ThemeComparisonJudgeEvaluator`'s prompt-building — but doesn't
shuffle (`shuffle` stays `False`) and isn't ternary decision-scored
(`decision_scored` stays `False`): it extracts two named numeric keys
directly via `ThemeComparisonJudgeEvaluator`'s shared `_build_scores`.

NOTE: this one LLM call scores two metrics (compression_quality,
information_retention) together, same as today's evaluators.py — one combined
prompt/response, one shared calibration example, purely to amortise
re-presenting the original/condensed topic lists, not because the two
metrics need joint reasoning — each has its own independent rubric.
Contrast with GroundednessEvaluator/CoverageEvaluator, which get one
metric each because their shared prompt is a single asymmetric matching
task that can't be split this way (see that pair's docstrings). Splitting
condensation's prompt into one call per metric is deliberately deferred —
see ADR-0013 (`docs/architecture/decisions/0013-modular-evaluation-framework-for-themefinder.md`)
— at which point this becomes two single-metric evaluators on the same
`ThemeComparisonJudgeEvaluator` base, same shape as groundedness/coverage.
"""

from prompts import condensation_eval_prompt

from .common import ThemeComparisonJudgeEvaluator


class CondensationQualityEvaluator(ThemeComparisonJudgeEvaluator):
    prompt_fn = staticmethod(condensation_eval_prompt)
    first_kwarg = "original_topics"
    second_kwarg = "condensed_topics"
    metric_names = ("compression_quality", "information_retention")
    # No ground truth to compare against — case.expected_output is always
    # None for condensation cases — so the pre-transform themes live on
    # case.inputs instead (see datasets.py::load_local_condensation_data).
    ground_truth_attr = "inputs"
