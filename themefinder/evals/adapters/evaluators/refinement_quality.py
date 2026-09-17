"""RefinementQualityEvaluator — four-dimension quality assessment of theme refinement.

Compares refined `output["themes"]` against the pre-refinement themes on
`case.inputs` (refinement has no ground truth). All four metrics currently
share one LLM call; splitting them per metric is deferred to ADR-0013.
"""

from prompts import refinement_eval_prompt

from .llm_judge import ThemeComparisonJudgeEvaluator


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
    # case.inputs instead (see datasets.py::load_local_condensation_data)
    ground_truth_attr = "inputs"
