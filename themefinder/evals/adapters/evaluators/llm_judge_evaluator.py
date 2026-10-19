"""Shared LLM-judge machinery
`LLMJudgeEvaluator` - base
`SinglePromptJudgeEvaluator`, `BinaryMatchJudgeEvaluator` - single-prompt and per-item judges
`ThemeComparisonJudgeEvaluator`, `DecisionScoredComparisonJudge`, the bases for concrete theme-comparison judges
"""

import asyncio
import json
import logging
import random
import re
from abc import abstractmethod
from collections.abc import Callable
from typing import Any

import numpy as np
import openai
from eval_types import Case, Score
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)
from utils.logging_config import get_logger

from .prompts import load_prompt_fn
from .base import EvaluatorPort

logger = get_logger(__name__)


class LLMJudgeEvaluator(EvaluatorPort):
    """Base for the LLM-as-judge evaluators: carries the judge LLM and the
    shared retry/parsing plumbing. Subclasses implement `_score` and
    `_build_scores`.
    """

    prompt_fn: Callable = None

    def __init__(self, llm: Any, shuffle: bool = False):
        """Store the injected judge LLM — any object with an async `ainvoke`
        returning a response with a `.parsed` string."""
        self.llm = llm
        self.shuffle = shuffle

    @retry(
        wait=wait_random_exponential(min=1, max=20),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(
            (
                openai.APIConnectionError,
                openai.RateLimitError,
                openai.InternalServerError,
            )
        ),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    async def invoke_with_retry(self, prompt: str) -> Any:
        """Invoke the judge LLM, retrying only on transient errors (connection,
        rate limit, 5xx); non-transient errors reraise immediately."""
        return await self.llm.ainvoke(prompt)

    @staticmethod
    def _parse_json_markdown(text: str) -> dict:
        """Extract JSON from markdown code fences or raw text."""
        match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
        return json.loads(match.group(1) if match else text)

    @staticmethod
    def _shuffle_themes(themes: list[dict]) -> list[dict]:
        """Shuffle a copy of theme records to reduce positional bias."""
        shuffled = list(themes)
        random.shuffle(shuffled)
        return shuffled

    @abstractmethod
    def _build_scores(self, decisions: Any) -> list[Score]:
        """Turn the parsed judge response into Scores."""


class SinglePromptJudgeEvaluator(LLMJudgeEvaluator):
    """Base for judges that build a single prompt per case/output and score the
    response by extracting one named numeric key per metric."""

    @abstractmethod
    def _build_prompt(self, case: Case, output: Any) -> str | None:
        """Build the judge prompt, or return None to skip the LLM call when
        there's nothing to evaluate."""

    async def _score(self, case: Case, output: Any) -> list[Score]:
        """Build the prompt, invoke the judge (skipping the call when
        `_build_prompt` returns None), parse the response, and score it."""
        prompt = self._build_prompt(case, output)
        if prompt is not None:
            response = await self.invoke_with_retry(prompt)
            parsed = self._parse_json_markdown(response.parsed)
        else:
            parsed: dict = {}

        return self._build_scores(parsed)


class ThemeComparisonJudgeEvaluator(SinglePromptJudgeEvaluator):
    """Base for judges that compare two theme lists in one LLM call, scoring
    the response by extracting one named numeric key per metric.
    """

    first_kwarg: str = "topic_list_1"
    second_kwarg: str = "topic_list_2"

    #: Name of the `Case` field holding this evaluator's case-side
    #: (ground-truth / pre-transform) themes.
    ground_truth_attr: str = "expected_output"

    def _topic_order(self, case_themes: Any, output_themes: Any) -> tuple[Any, Any]:
        """Order the two theme lists, case-side first by default; subclasses
        override to swap."""
        return case_themes, output_themes

    def _build_prompt(self, case: Case, output: Any) -> str:
        """Retrieve the case-side and output-side theme lists, order and
        optionally shuffle them, and pass them to `prompt_fn`."""
        case_side = getattr(case, self.ground_truth_attr) or {}
        case_themes = case_side.get("themes", [])
        output_themes = output.get("themes", [])
        topic_list_1, topic_list_2 = self._topic_order(case_themes, output_themes)
        if self.shuffle:
            topic_list_1 = self._shuffle_themes(topic_list_1)
            topic_list_2 = self._shuffle_themes(topic_list_2)
        return self.prompt_fn(
            **{self.first_kwarg: topic_list_1, self.second_kwarg: topic_list_2}
        )

    def _build_scores(self, decisions: Any) -> list[Score]:
        """Extract one Score per metric from the parsed response, reading its
        numeric value and `{metric}_reasoning` comment."""
        return [
            Score(
                metric,
                round(float(decisions.get(metric, 0)), 2),
                decisions.get(f"{metric}_reasoning", ""),
            )
            for metric in self.metric_names
        ]


# Minimum score (0-5) to consider a topic well-grounded or captured, for the
# decision-scored judges below.
GROUNDEDNESS_THRESHOLD = 3

# Score mapping from ternary decisions to numeric values (0-5 scale).
DECISION_SCORES = {
    "STRONG": 5,
    "PARTIAL": 3,
    "NO": 0,
}


class DecisionScoredComparisonJudge(ThemeComparisonJudgeEvaluator):
    """Theme-comparison judge whose prompt asks for per-theme STRONG/PARTIAL/NO
    decisions, mapped to 0-5 and averaged into a single metric.
    """

    #: Phrase used in the comment summary, e.g. "themes below threshold".
    threshold_label: str = ""

    def _build_scores(self, decisions: Any) -> list[Score]:
        """Map the parsed per-theme STRONG/PARTIAL/NO decisions to a single
        averaged 0-5 metric with an enriched comment."""
        result = self._decision_score(decisions)
        metric_name = self.metric_names[0]
        comment = self._build_comment(result)
        return [Score(metric_name, round(result["average"], 2), comment)]

    def _decision_score(self, parsed: dict) -> dict[str, Any]:
        """Turn a parsed STRONG/PARTIAL/NO decision response into numeric
        scores, their average, threshold counts, and per-topic details."""
        evaluations = parsed.get("evaluations", parsed)

        scores = []
        details = []

        for theme_label, evaluation in evaluations.items():
            if isinstance(evaluation, dict):
                decision = evaluation.get("decision", "NO").upper()
                score = DECISION_SCORES.get(decision, 0)
                scores.append(score)
                details.append(
                    {
                        "theme": theme_label,
                        "matched_to": evaluation.get("matched_to", "none"),
                        "decision": decision,
                        "reasoning": evaluation.get("reasoning", ""),
                        "score": score,
                    }
                )
            elif isinstance(evaluation, (int, float)):
                # Backwards compatibility with old 0-5 format
                scores.append(evaluation)
                details.append(
                    {
                        "theme": theme_label,
                        "decision": "LEGACY",
                        "score": evaluation,
                    }
                )

        return {
            "scores": scores,
            "average": float(np.mean(scores)) if scores else 0.0,
            "n_below_threshold": sum(s < GROUNDEDNESS_THRESHOLD for s in scores),
            "n_total": len(scores),
            "details": details,
        }

    def _build_comment(self, result: dict[str, Any]) -> str:
        """Build a comment from the decision details: a threshold summary
        followed by one line per theme (summary only for the legacy format)."""
        summary = (
            f"{result['n_below_threshold']}/{result['n_total']} {self.threshold_label}"
        )

        details = result.get("details", [])
        if not details or details[0].get("decision") == "LEGACY":
            return summary

        decision_parts = []
        for detail in details:
            decision = detail.get("decision", "?")
            theme = detail.get("theme", "?")
            matched = detail.get("matched_to", "none")
            reasoning = detail.get("reasoning", "")
            if decision == "NO":
                decision_parts.append(f"  {decision}: {theme} (no match) — {reasoning}")
            else:
                decision_parts.append(
                    f"  {decision}: {theme} → {matched} — {reasoning}"
                )

        return f"{summary}\n" + "\n".join(decision_parts)


class BinaryMatchJudgeEvaluator(LLMJudgeEvaluator):
    """Base for judges that ask, once per item in the first list, whether it
    matches any item in the second list, yielding one YES/NO decision per item.
    Subclasses implement `_get_lists`, and `_build_scores` and set the prompt_fn.
    """

    prompt_fn = staticmethod(load_prompt_fn("binary_match"))

    def __init__(self, *args, concurrency: int = 5, **kwargs):
        """Store the injected judge LLM and the concurrency limit for LLM calls."""
        super().__init__(*args, **kwargs)
        self.concurrency = concurrency

    @abstractmethod
    def _get_lists(self, case: Case, output: Any) -> tuple[list[str], list[str]]:
        """Return (items to judge, candidate list) from the case and output;
        subclasses choose which lists and in which direction."""

    def _build_item_prompt(self, single_item: str, item_list: list[str]) -> str:
        """Build the prompt asking whether `single_item` matches any of `item_list`."""
        return self.prompt_fn(single_item=single_item, candidate_list=item_list)

    async def _single_item_decision(
        self, single_item: str, item_list: list[str], sem: asyncio.Semaphore
    ) -> dict[str, Any]:
        """Ask the judge once whether `single_item` matches any of `item_list`,
        under the shared semaphore so the loop stays within rate limits."""
        async with sem:
            if self.shuffle:
                item_list = self._shuffle_themes(item_list)
            prompt = self._build_item_prompt(single_item, item_list)
            response = await self.invoke_with_retry(prompt)
            parsed = self._parse_json_markdown(response.parsed)
            return {**parsed, "item": single_item, "item_list": item_list}

    async def _llm_decision_loop(
        self, items: list[str], comparison_items: list[str]
    ) -> list[dict[str, Any]]:
        """Judge every item against `comparison_items` concurrently; Any failure
        raises and aborts the whole loop."""
        if not items or not comparison_items:
            logger.error("No items or comparison items provided for LLM decision loop.")
            raise ValueError(
                "No items or comparison items provided for LLM decision loop."
            )

        sem = asyncio.Semaphore(self.concurrency)
        tasks = [
            asyncio.create_task(self._single_item_decision(item, comparison_items, sem))
            for item in items
        ]
        try:
            return await asyncio.gather(*tasks)
        except Exception:
            # gather re-raises the first failure but leaves its siblings running;
            # cancel them and wait so none are orphaned. TODO: TaskGroup
            # does this natively, use it once the package floor is Python 3.11.
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            raise

    async def _score(self, case: Case, output: Any) -> list[Score]:
        """Get the two lists, judge each item in the first against the second,
        and hand the per-item decisions to `_build_scores`."""
        list1, list2 = self._get_lists(case, output)

        # Get the LLM's decisions for each item in list1 as compared to list2
        decisions = await self._llm_decision_loop(list1, list2)

        # Implemented in subclasses: convert the LLM's decisions into scores
        scores = self._build_scores(decisions)

        return scores
