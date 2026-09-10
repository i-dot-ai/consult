"""RefinementQualityEvaluator — four-dimension quality assessment of theme refinement.

Compares `output["themes"]` (refined) against `case.inputs["themes"]` (the
pre-refinement themes) — not `case.expected_output`, for the same reason as
CondensationQualityEvaluator: refinement has no ground truth to compare
against, only a before/after pair.

NOTE: this one LLM call scores four metrics (information_retention,
response_references, distinctiveness, fluency) together, same as today's
evaluators.py — one combined prompt/response, one shared calibration example.
Splitting this into one prompt per metric is deliberately deferred to a later
issue reviewing the LLM-as-judge prompts themselves; see prompts.py's
refinement_eval_prompt.
"""

import logging
from typing import Any

from eval_types import Case, Score
from prompts import refinement_eval_prompt

from .common import LLMJudgeEvaluator

logger = logging.getLogger(__name__)

REFINEMENT_METRICS = (
    "information_retention",
    "response_references",
    "distinctiveness",
    "fluency",
)


class RefinementQualityEvaluator(LLMJudgeEvaluator):
    prompt_fn = staticmethod(refinement_eval_prompt)

    async def evaluate(self, case: Case, output: Any) -> list[Score]:
        try:
            original_themes = case.inputs.get("themes", [])
            refined_themes = output.get("themes", [])

            response = await self.invoke_with_retry(
                self.prompt_fn(
                    original_topics=original_themes, new_topics=refined_themes
                )
            )
            parsed = self._parse_json_markdown(response.parsed)

            return [
                Score(
                    metric,
                    round(float(parsed.get(metric, 0)), 2),
                    parsed.get(f"{metric}_reasoning", ""),
                )
                for metric in REFINEMENT_METRICS
            ]
        except Exception as e:
            logger.error(f"Refinement quality evaluation failed: {e}")
            return [Score(metric, 0.0, f"Error: {e}") for metric in REFINEMENT_METRICS]
