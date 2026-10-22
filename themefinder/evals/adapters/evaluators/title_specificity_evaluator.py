"""TitleSpecificityEvaluator — per-title binary specificity assessment."""

import asyncio
from typing import Any

from eval_types import Case, Score

from .llm_judge_evaluator import LLMJudgeEvaluator
from .prompts import load_prompt_fn


class TitleSpecificityEvaluator(LLMJudgeEvaluator):
    prompt_fn = staticmethod(load_prompt_fn("title_specificity"))
    metric_names = ("specificity",)

    def __init__(self, *args, concurrency: int = 5, **kwargs):
        super().__init__(*args, **kwargs)
        self.concurrency = concurrency

    async def _single_title_decision(
        self, title: str, sem: asyncio.Semaphore
    ) -> dict[str, str]:
        """Judge one title while respecting the evaluator's concurrency limit."""
        async with sem:
            response = await self.invoke_with_retry(self.prompt_fn(theme_title=title))
        parsed = self._parse_json_markdown(response.parsed)
        return self._parse_decision(title, parsed)

    async def _score(self, case: Case, output: Any) -> list[Score]:
        """Judge each generated title independently."""
        del case
        titles = self.extract_theme_titles(output.get("themes", []))
        sem = asyncio.Semaphore(self.concurrency)
        tasks = [
            asyncio.create_task(self._single_title_decision(title, sem))
            for title in titles
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
    def _parse_decision(title: str, parsed: Any) -> dict[str, str]:
        """Validate a single binary decision from the specificity judge."""
        if not isinstance(parsed, dict):
            raise TypeError("Specificity judge response must be a JSON object")

        decision = parsed.get("decision")
        reasoning = parsed.get("reasoning")
        if decision not in {"PASS", "FAIL"}:
            raise ValueError(f"Specificity decision for {title!r} must be PASS or FAIL")
        if not isinstance(reasoning, str):
            raise TypeError(f"Specificity reasoning for {title!r} must be a string")

        return {"title": title, "decision": decision, "reasoning": reasoning}

    def _build_scores(self, decisions: list[dict[str, str]]) -> list[Score]:
        """Return the proportion of independently judged titles that pass."""
        n_pass = sum(decision["decision"] == "PASS" for decision in decisions)
        n_total = len(decisions)
        ratio = n_pass / n_total if n_total else 0.0

        comment = f"{n_pass}/{n_total} titles passed"
        failed_titles = [
            decision["title"]
            for decision in decisions
            if decision["decision"] == "FAIL"
        ]
        if failed_titles:
            comment += f"\nFailed: {', '.join(failed_titles)}"

        return [Score("specificity", round(ratio, 2), comment)]
