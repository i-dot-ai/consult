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
evaluators.py — one combined prompt/response, one shared calibration
example, purely to amortise re-presenting the original/refined topic
lists, not because the metrics need joint reasoning — each has its own
independent rubric (and distinctiveness/fluency don't even read
`original_topics`, a natural split point already inside the prompt).
Contrast with GroundednessEvaluator/CoverageEvaluator, which get one
metric each because their shared prompt is a single asymmetric matching
task that can't be split this way (see that pair's docstrings). Splitting
refinement's prompt into one call per metric is deliberately deferred —
see ADR-0013 (`docs/architecture/decisions/0013-modular-evaluation-framework-for-themefinder.md`)
— at which point this becomes four single-metric evaluators on the same
`ThemeComparisonJudgeEvaluator` base, same shape as groundedness/coverage.
"""

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
    # No ground truth to compare against — case.expected_output is always
    # None for refinement cases — so the pre-transform themes live on
    # case.inputs instead (see datasets.py::load_local_condensation_data,
    # which refinement's loader reuses).
    ground_truth_attr = "inputs"
