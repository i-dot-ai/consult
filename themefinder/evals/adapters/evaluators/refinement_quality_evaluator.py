"""LLM-judge evaluators for refinement quality and per-theme clarity.

Compares refined `output["themes"]` against the pre-refinement themes on
`case.inputs` (refinement has no ground truth). The comparison evaluator scores
the three criteria that require both theme sets. Clarity is evaluated
independently for each refined theme.
"""

import asyncio
from typing import Any

from eval_types import Case, Score

from .llm_judge_evaluator import LLMJudgeEvaluator, ThemeComparisonJudgeEvaluator
from .prompts import load_prompt_fn


class RefinementQualityEvaluator(ThemeComparisonJudgeEvaluator):
    prompt_fn = staticmethod(load_prompt_fn("refinement"))
    first_kwarg = "original_topics"
    second_kwarg = "new_topics"
    metric_names = (
        "information_retention",
        "response_references",
        "distinctiveness",
    )
    # No ground truth to compare against — case.expected_output is always
    # None for refinement cases — so the pre-transform themes live on
    # case.inputs instead (see datasets.py::load_local_condensation_data)
    ground_truth_attr = "inputs"


class ClarityEvaluator(LLMJudgeEvaluator):
    """Evaluate each refined theme independently for simple, clear wording."""

    prompt_fn = staticmethod(load_prompt_fn("clarity"))
    metric_names = ("clarity",)

    def __init__(self, *args, concurrency: int = 5, **kwargs):
        super().__init__(*args, **kwargs)
        self.concurrency = concurrency

    @staticmethod
    def _theme_label(theme: dict[str, Any]) -> str:
        return theme.get("topic_label", theme.get("topic", ""))

    async def _judge_theme(
        self, theme: dict[str, Any], sem: asyncio.Semaphore
    ) -> dict[str, str]:
        """Judge one theme under the shared concurrency limit."""
        label = self._theme_label(theme)
        description = theme.get("topic_description", "")

        async with sem:
            response = await self.invoke_with_retry(
                self.prompt_fn(
                    topic_label=label,
                    topic_description=description,
                )
            )

        parsed = self._parse_json_markdown(response.parsed)
        decision = parsed.get("decision")
        reasoning = parsed.get("reasoning")
        if decision not in {"PASS", "FAIL"}:
            raise ValueError("Clarity decision must be exactly PASS or FAIL")
        if not isinstance(reasoning, str):
            raise TypeError("Clarity reasoning must be a string")

        return {"label": label, "decision": decision, "reasoning": reasoning}

    def _build_scores(self, decisions: list[dict[str, str]]) -> list[Score]:
        """Turn individual decisions into a passing proportion and failure details."""
        n_total = len(decisions)
        n_pass = sum(decision["decision"] == "PASS" for decision in decisions)
        comment = f"{n_pass}/{n_total} themes clear"

        failures = [
            decision for decision in decisions if decision["decision"] == "FAIL"
        ]
        if failures:
            comment += "\n" + "\n".join(
                f"FAIL: {failure['label']} — {failure['reasoning']}"
                for failure in failures
            )

        score = n_pass / n_total if n_total else 0.0
        return [Score("clarity", round(score, 2), comment)]

    async def _score(self, case: Case, output: Any) -> list[Score]:
        """Judge every refined theme independently, skipping empty outputs."""
        del case
        themes = output.get("themes", [])
        if not themes:
            return self._build_scores([])

        sem = asyncio.Semaphore(self.concurrency)
        tasks = [asyncio.create_task(self._judge_theme(theme, sem)) for theme in themes]
        try:
            decisions = await asyncio.gather(*tasks)
        except Exception:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            raise

        return self._build_scores(decisions)
