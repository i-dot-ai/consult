"""TitleSpecificityEvaluator — how specific/concrete generated theme titles are.

Ignores `case` entirely — scores the specificity of `output["themes"]`'s titles
alone, matching today's `create_title_specificity_evaluator` (which accepts an
`expected_output` kwarg for shape compatibility but never reads it).
"""

import logging
from typing import Any

from eval_types import Case, Score
from prompts import title_specificity_eval_prompt

from .common import LLMJudgeEvaluator

logger = logging.getLogger(__name__)


class TitleSpecificityEvaluator(LLMJudgeEvaluator):
    prompt_fn = staticmethod(title_specificity_eval_prompt)

    async def evaluate(self, case: Case, output: Any) -> list[Score]:
        try:
            themes = output.get("themes", [])
            if isinstance(themes, list):
                titles = [t.get("topic_label", t.get("topic", "")) for t in themes]
            elif isinstance(themes, dict):
                titles = list(themes.keys())
            else:
                titles = []

            if not titles:
                return [Score("specificity", 0.0, "0/0 titles specific")]

            response = await self.invoke_with_retry(self.prompt_fn(theme_titles=titles))
            parsed = self._parse_json_markdown(response.parsed)
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
        except Exception as e:
            logger.error(f"Specificity evaluation failed: {e}")
            return [Score("specificity", 0.0, f"Error: {e}")]
