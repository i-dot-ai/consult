"""CondensationQualityEvaluator — compression quality + information retention when
condensing a large theme set into a smaller one.

Compares condensed `output["themes"]` against the pre-condensation themes on
`case.inputs` (condensation has no ground truth). Both metrics currently share
one LLM call; splitting them per metric is deferred to PRO-642 if required.
"""

from prompts import condensation_eval_prompt

from .llm_judge import ThemeComparisonJudgeEvaluator


class CondensationQualityEvaluator(ThemeComparisonJudgeEvaluator):
    prompt_fn = staticmethod(condensation_eval_prompt)
    first_kwarg = "original_topics"
    second_kwarg = "condensed_topics"
    metric_names = ("compression_quality", "information_retention")
    # No ground truth to compare against — case.expected_output is always
    # None for condensation cases — so the pre-transform themes live on
    # case.inputs instead
    ground_truth_attr = "inputs"
