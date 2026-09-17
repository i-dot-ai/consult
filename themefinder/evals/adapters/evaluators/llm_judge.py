"""Shared LLM-judge machinery: `LLMJudgeEvaluator`, `ThemeComparisonJudgeEvaluator`
and `DecisionScoredComparisonJudge`, the bases for the concrete judge adapters
in the sibling files.
"""

import json
import logging
import random
import re
from typing import Any, Function
from abc import abstractmethod

import numpy as np
import openai
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from eval_types import Case, Score
from .base import EvaluatorPort

logger = logging.getLogger(__name__)


class LLMJudgeEvaluator(EvaluatorPort):
    """Base for the LLM-as-judge evaluators: carries the judge LLM and the
    shared retry/parsing plumbing. Subclasses implement `_build_prompt` and
    `_build_scores`.
    """

    shuffle: bool = False
    prompt_fn: Function = None

    def __init__(self, llm: Any):
        """Store the injected judge LLM — any object with an async `ainvoke`
        returning a response with a `.parsed` string."""
        self.llm = llm

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
    def _shuffle_themes(themes: list[dict] | dict) -> list[dict] | dict:
        """Shuffle theme order to reduce positional bias, returning a copy in
        the same shape (list or label-keyed dict) as the input.
        TODO (PRO-734): can be simplified once all themes are dicts."""

        if isinstance(themes, list):
            shuffled = list(themes)
            random.shuffle(shuffled)
            return shuffled

        if isinstance(themes, dict):
            keys = list(themes.keys())
            random.shuffle(keys)
            return {k: themes[k] for k in keys}

        return themes

    @abstractmethod
    def _build_prompt(self, case: Case, output: Any) -> str | None:
        """Build the judge prompt, or return None to skip the LLM call when
        there's nothing to evaluate."""

    @abstractmethod
    def _build_scores(self, parsed: dict) -> list[Score]:
        """Turn the parsed judge response into Scores."""

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


class ThemeComparisonJudgeEvaluator(LLMJudgeEvaluator):
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

    def _build_scores(self, parsed: dict) -> list[Score]:
        """Extract one Score per metric from the parsed response, reading its
        numeric value and `{metric}_reasoning` comment."""
        return [
            Score(
                metric,
                round(float(parsed.get(metric, 0)), 2),
                parsed.get(f"{metric}_reasoning", ""),
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

    def _build_scores(self, parsed: dict) -> list[Score]:
        """Map the parsed per-theme STRONG/PARTIAL/NO decisions to a single
        averaged 0-5 metric with an enriched comment."""
        result = self._decision_score(parsed)
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
