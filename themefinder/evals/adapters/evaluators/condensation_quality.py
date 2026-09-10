"""CondensationQualityEvaluator — compression quality + information retention when
condensing a large theme set into a smaller one.

Compares `output["themes"]` (condensed) against `case.inputs["themes"]` (the
pre-condensation themes) — not `case.expected_output`, which is `None` for
condensation cases (no ground truth; see `datasets.py::load_local_condensation_data`).

NOTE: this one LLM call scores two metrics (compression_quality,
information_retention) together, same as today's evaluators.py — one combined
prompt/response, one shared calibration example. Splitting this into one
prompt per metric is deliberately deferred to a later issue reviewing the
LLM-as-judge prompts themselves; see prompts.py's condensation_eval_prompt.
"""

import logging
from typing import Any

from eval_types import Case, Score
from prompts import condensation_eval_prompt

from .common import LLMJudgeEvaluator

logger = logging.getLogger(__name__)

CONDENSATION_METRICS = ("compression_quality", "information_retention")


class CondensationQualityEvaluator(LLMJudgeEvaluator):
    prompt_fn = staticmethod(condensation_eval_prompt)

    async def evaluate(self, case: Case, output: Any) -> list[Score]:
        try:
            original_themes = case.inputs.get("themes", [])
            condensed_themes = output.get("themes", [])

            response = await self.invoke_with_retry(
                self.prompt_fn(
                    original_topics=original_themes,
                    condensed_topics=condensed_themes,
                )
            )
            parsed = self._parse_json_markdown(response.parsed)

            return [
                Score(
                    metric,
                    round(float(parsed.get(metric, 0)), 2),
                    parsed.get(f"{metric}_reasoning", ""),
                )
                for metric in CONDENSATION_METRICS
            ]
        except Exception as e:
            logger.error(f"Condensation quality evaluation failed: {e}")
            return [
                Score(metric, 0.0, f"Error: {e}") for metric in CONDENSATION_METRICS
            ]
