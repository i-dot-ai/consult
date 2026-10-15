"""GroundednessEvaluator — how well generated themes are grounded in expected themes.

Sibling of CoverageEvaluator, which scores the reverse direction.
"""

from typing import Any

from prompts.generation import (
    generation_eval_prompt,
    generation_groundedness_eval_prompt,
)

from eval_types import Score
from .llm_judge_evaluator import (
    DecisionScoredComparisonJudge,
    BinaryMatchJudgeEvaluator,
)


class GroundednessSinglePromptEvaluator(DecisionScoredComparisonJudge):
    prompt_fn = staticmethod(generation_eval_prompt)
    metric_names = ("groundedness",)
    threshold_label = "themes below threshold"

    def __init__(self, *args, shuffle: bool = True, **kwargs):
        super().__init__(*args, **kwargs, shuffle=shuffle)

    def _topic_order(self, case_themes: Any, output_themes: Any) -> tuple[Any, Any]:
        """Score generated (output) themes against expected (case) themes, so
        output goes first."""
        return output_themes, case_themes


class GroundednessThemesFromResponsesEvaluator(BinaryMatchJudgeEvaluator):
    prompt_fn = staticmethod(generation_groundedness_eval_prompt)

    def _get_lists(self, case: Any, output: Any) -> tuple[list[str], list[str]]:
        """Return the intput responses and the generated themes as lists of strings for comparison."""
        input_responses = [
            response["text"] for response in case.inputs.get("responses", [])
        ]
        generated_themes = [theme["title"] for theme in output.get("themes", [])]
        return generated_themes, input_responses

    def _build_item_prompt(self, single_item: str, item_list: list[str]) -> str:
        """Build the prompt for a single generated theme against the expected themes."""
        return self.prompt_fn(generated_theme=single_item, expected_themes=item_list)

    def _build_scores(self, decisions: Any) -> list:
        """Return the fraction of generated themes judged grounded as the score,
        listing any ungrounded themes in the comment."""
        n_grounded = sum(d.get("decision") == "YES" for d in decisions)
        n_total = len(decisions)
        ratio = n_grounded / n_total if n_total > 0 else 0.0

        ungrounded_themes = [
            d.get("item") for d in decisions if d.get("decision") != "YES"
        ]
        comment = f"{n_grounded}/{n_total} themes grounded"
        if ungrounded_themes:
            comment += f"\nUngrounded: {', '.join(ungrounded_themes)}"

        return [Score("groundedness", round(ratio, 2), comment)]
