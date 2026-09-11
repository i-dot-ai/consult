"""TitleSpecificityEvaluator — how specific/concrete generated theme titles are.

Ignores `case` entirely — scores the specificity of `output["themes"]`'s titles
alone, matching today's `create_title_specificity_evaluator` (which accepts an
`expected_output` kwarg for shape compatibility but never reads it).
"""

from typing import Any

from eval_types import Case, Score
from prompts import title_specificity_eval_prompt

from .common import LLMJudgeEvaluator


class TitleSpecificityEvaluator(LLMJudgeEvaluator):
    prompt_fn = staticmethod(title_specificity_eval_prompt)
    metric_names = ("specificity",)

    def _build_prompt(self, case: Case, output: Any) -> str | None:
        titles = self.extract_theme_titles(output.get("themes", []))

        if not titles:
            # Nothing to evaluate — skip the LLM call entirely. `evaluate()`
            # then runs `_build_scores({})` below, which naturally produces
            # "0/0 titles specific" without any special-casing here.
            return None

        return self.prompt_fn(theme_titles=titles)

    def _build_scores(self, parsed: dict) -> list[Score]:
        evaluations = parsed.get("evaluations", parsed)

        n_specific = 0
        vague_titles = []
        for title, evaluation in evaluations.items():
            decision = evaluation.get("decision", "VAGUE").upper()
            if decision == "SPECIFIC":
                n_specific += 1
            else:
                vague_titles.append(title)

        n_total = len(evaluations)
        ratio = n_specific / n_total if n_total > 0 else 0.0

        comment = f"{n_specific}/{n_total} titles specific"
        if vague_titles:
            comment += f"\nVague: {', '.join(vague_titles)}"

        return [Score("specificity", round(ratio, 2), comment)]
