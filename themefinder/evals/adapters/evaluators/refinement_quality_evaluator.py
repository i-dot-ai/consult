"""RefinementQualityEvaluator — two-dimension quality assessment of theme refinement.

Compares refined `output["themes"]` against the pre-refinement themes on
`case.inputs` (refinement has no ground truth). Both metrics currently
share one LLM call; splitting them per metric is deferred to ADR-0013.
"""

from .llm_judge_evaluator import ThemeComparisonJudgeEvaluator
from .prompts import load_prompt_fn


class RefinementQualityEvaluator(ThemeComparisonJudgeEvaluator):
    prompt_fn = staticmethod(load_prompt_fn("refinement"))
    first_kwarg = "original_topics"
    second_kwarg = "new_topics"
    metric_names = (
        "response_references",
        "distinctiveness",
    )
    # No ground truth to compare against — case.expected_output is always
    # None for refinement cases — so the pre-transform themes live on
    # case.inputs instead (see datasets.py::load_local_condensation_data)
    ground_truth_attr = "inputs"
