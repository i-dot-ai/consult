"""ClarityEvaluator — per-theme binary clarity assessment."""

import asyncio
from typing import Any

from eval_types import Case, Score

from .llm_judge_evaluator import LLMJudgeEvaluator
from .prompts import load_prompt_fn


class ClarityEvaluator(LLMJudgeEvaluator):
    """Judge each refined theme independently for simple, clear wording."""

    prompt_fn = staticmethod(load_prompt_fn("clarity"))
    metric_names = ("clarity",)

    def __init__(self, *args, concurrency: int = 5, **kwargs):
        super().__init__(*args, **kwargs)
        self.concurrency = concurrency

    async def _single_theme_decision(
        self, theme: dict[str, str], sem: asyncio.Semaphore
    ) -> dict[str, str]:
        """Judge one theme while respecting the evaluator's concurrency limit."""
        label = theme.get("topic_label", "")
        description = theme.get("topic_description", "")
        async with sem:
            response = await self.invoke_with_retry(
                self.prompt_fn(topic_label=label, topic_description=description)
            )
        parsed = self._parse_json_markdown(response.parsed)
        return self._parse_decision(label, parsed)

    async def _score(self, case: Case, output: Any) -> list[Score]:
        """Judge each refined theme independently."""
        del case
        themes = output.get("themes", [])
        sem = asyncio.Semaphore(self.concurrency)
        tasks = [
            asyncio.create_task(self._single_theme_decision(theme, sem))
            for theme in themes
        ]
        try:
            decisions = await asyncio.gather(*tasks)
        except Exception:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            raise

        return self._build_scores(decisions)

    @staticmethod
    def _parse_decision(label: str, parsed: Any) -> dict[str, str]:
        """Validate a single binary decision from the clarity judge."""
        if not isinstance(parsed, dict):
            raise TypeError("Clarity judge response must be a JSON object")

        decision = parsed.get("decision")
        reasoning = parsed.get("reasoning")
        if decision not in {"PASS", "FAIL"}:
            raise ValueError(f"Clarity decision for {label!r} must be PASS or FAIL")
        if not isinstance(reasoning, str):
            raise TypeError(f"Clarity reasoning for {label!r} must be a string")

        return {"label": label, "decision": decision, "reasoning": reasoning}

    def _build_scores(self, decisions: list[dict[str, str]]) -> list[Score]:
        """Return the proportion of independently judged themes that pass."""
        n_pass = sum(decision["decision"] == "PASS" for decision in decisions)
        n_total = len(decisions)
        ratio = n_pass / n_total if n_total else 0.0

        comment = f"{n_pass}/{n_total} themes passed"
        failures = [
            decision for decision in decisions if decision["decision"] == "FAIL"
        ]
        if failures:
            comment += "\nFailed:\n" + "\n".join(
                f"  {failure['label']} — {failure['reasoning']}" for failure in failures
            )

        return [Score("clarity", round(ratio, 2), comment)]
