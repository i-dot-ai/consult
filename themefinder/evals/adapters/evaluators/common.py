"""Shared LLM-judge machinery: `LLMJudgeEvaluator` and `ThemeComparisonJudgeEvaluator`.

Moved from `evaluators.py` (behaviour-preserving, not byte-identical — the
old factory closures and module-level helper functions become methods on
this class hierarchy). The five LLM-judge `EvaluatorPort` subclasses live in
their own sibling files: groundedness.py, coverage.py, title_specificity.py,
condensation_quality.py, refinement_quality.py.

`_shuffle_themes`/`_parse_evaluation_response`/`_build_comment` are only
actually used by `ThemeComparisonJudgeEvaluator` (groundedness + coverage);
`_parse_json_markdown` is generic across all five. Everything here is a
method, not a free function — callers use `self._parse_json_markdown(...)`
etc., consistent with `invoke_with_retry`.
"""

import json
import logging
import random
import re
from typing import Any

import numpy as np
import openai
from eval_types import Case, Score
from prompts import generation_eval_prompt
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from .base import EvaluatorPort

logger = logging.getLogger(__name__)

# Minimum score (0-5) to consider a topic well-grounded or captured
GROUNDEDNESS_THRESHOLD = 3

# Score mapping from ternary decisions to numeric values (0-5 scale)
DECISION_SCORES = {
    "STRONG": 5,
    "PARTIAL": 3,
    "NO": 0,
}


class LLMJudgeEvaluator(EvaluatorPort):
    """Base for the five LLM-as-judge evaluators — carries the judge LLM and
    the shared retry-on-transient-error / JSON-parsing plumbing every one of
    them needs."""

    def __init__(self, llm: Any):
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
        """Call self.llm.ainvoke(), retrying on transient connection errors.

        OpenAILLM.invoke()'s sync wrapper spins up a fresh event loop per call
        while reusing a single shared AsyncOpenAI client - the client's
        connection pool is bound to whichever loop first touched it, so reusing
        it from a different loop occasionally raises a spurious
        APIConnectionError. Calling ainvoke() directly (we're always inside a
        running loop here) avoids that entirely; the retry is a backstop for
        ordinary transient network issues, same as llm_batch_processor.py.

        Only retries connection errors, rate limits, and server-side 5xxs -
        APIConnectionError's own subclass APITimeoutError is covered too.
        Non-transient errors (bad request, auth, etc.) reraise immediately
        instead of burning retry attempts on something that won't change.
        """
        return await self.llm.ainvoke(prompt)

    @staticmethod
    def _parse_json_markdown(text: str) -> dict:
        """Extract JSON from markdown code fences or raw text."""
        match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
        return json.loads(match.group(1) if match else text)


class ThemeComparisonJudgeEvaluator(LLMJudgeEvaluator):
    """Base for groundedness/coverage — the only two LLM-judge evaluators that
    share the same shape: shuffle two theme lists, compare them via
    `generation_eval_prompt`, parse the binary decision response, and emit a
    single Score. Subclasses set `metric_name` and implement `_topic_lists` —
    no boolean "reverse" flag; each subclass just states its own
    (topic_list_1, topic_list_2) directly. See groundedness.py / coverage.py.
    """

    metric_name: str
    prompt_fn = staticmethod(generation_eval_prompt)

    def _topic_lists(self, case: Case, output: Any) -> tuple[Any, Any]:
        raise NotImplementedError

    @staticmethod
    def _shuffle_themes(themes: list[dict] | dict) -> list[dict] | dict:
        """Shuffle theme order to reduce positional bias in LLM-as-judge.

        Args:
            themes: Themes as a list of dicts or a dict keyed by label.

        Returns:
            Shuffled copy in the same format as input.
        """
        if isinstance(themes, list):
            shuffled = list(themes)
            random.shuffle(shuffled)
            return shuffled

        if isinstance(themes, dict):
            keys = list(themes.keys())
            random.shuffle(keys)
            return {k: themes[k] for k in keys}

        return themes

    def _parse_evaluation_response(self, response_content: str) -> dict[str, Any]:
        """Parse the binary judgment response from the generation eval prompt.

        Extracts per-theme evaluations and maps decisions to numeric scores.

        Args:
            response_content: Raw JSON response from the judge LLM.

        Returns:
            Dict with scores, average, threshold counts, and per-theme details.
        """
        parsed = self._parse_json_markdown(response_content)
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

    @staticmethod
    def _build_comment(result: dict[str, Any], metric_name: str) -> str:
        """Build an enriched comment string from evaluation details.

        Args:
            result: Parsed evaluation result from _parse_evaluation_response.
            metric_name: Either "groundedness" or "coverage".

        Returns:
            Comment string with threshold summary and per-theme decisions.
        """
        threshold_label = (
            "themes below threshold"
            if metric_name == "groundedness"
            else "themes not captured"
        )
        summary = f"{result['n_below_threshold']}/{result['n_total']} {threshold_label}"

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

    async def evaluate(self, case: Case, output: Any) -> list[Score]:
        try:
            topic_list_1, topic_list_2 = self._topic_lists(case, output)
            shuffled_1 = self._shuffle_themes(topic_list_1)
            shuffled_2 = self._shuffle_themes(topic_list_2)

            response = await self.invoke_with_retry(
                self.prompt_fn(topic_list_1=shuffled_1, topic_list_2=shuffled_2)
            )
            result = self._parse_evaluation_response(response.parsed)
            comment = self._build_comment(result, self.metric_name)
            return [Score(self.metric_name, round(result["average"], 2), comment)]
        except Exception as e:
            logger.error(f"{self.metric_name} evaluation failed: {e}")
            return [Score(self.metric_name, 0.0, f"Error: {e}")]
