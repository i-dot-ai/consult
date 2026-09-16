"""Shared LLM-judge machinery: `LLMJudgeEvaluator`, `ThemeComparisonJudgeEvaluator`
and `DecisionScoredComparisonJudge`.

Moved from `evaluators.py` (behaviour-preserving, not byte-identical — the
old factory closures and module-level helper functions become methods on
this class hierarchy). The five LLM-judge `EvaluatorPort` subclasses live in
their own sibling files: groundedness.py, coverage.py, title_specificity.py,
condensation_quality.py, refinement_quality.py.

`LLMJudgeEvaluator._score()` is the shared template every judge runs through;
`_build_scores` is the single scoring hook each judge implements for its own
response shape. The error boundary — catch, log, zero-score fallback — lives
on `EvaluatorPort.evaluate()`, not here.
"""

import json
import logging
import random
import re
from typing import Any
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
    """Base for the LLM-as-judge evaluators: carries the judge LLM, the shared
    retry/parsing plumbing, and the `_score()` template. Subclasses set a
    `prompt_fn` and `metric_names`, and implement `_build_prompt` (build the
    judge prompt, or return None to skip the call) and `_build_scores` (turn
    the parsed response into Scores).
    """

    shuffle: bool = False

    def __init__(self, llm: Any):
        """Store the injected judge LLM — any object exposing an async
        `ainvoke(prompt)` that returns a response with a `.parsed` string."""
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

    @staticmethod
    def _shuffle_themes(themes: list[dict] | dict) -> list[dict] | dict:
        """Shuffle theme order to reduce positional bias in LLM-as-judge.

        Only called by subclasses with `shuffle = True`.

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

    @abstractmethod
    def _build_prompt(self, case: Case, output: Any) -> str | None:
        """Build the judge prompt, or None to skip the LLM call entirely
        (nothing to evaluate). Every subclass implements this."""

    @abstractmethod
    def _build_scores(self, parsed: dict) -> list[Score]:
        """Turn the parsed judge response into Scores — the single scoring
        hook `_score()` always calls. Every leaf evaluator implements this
        (directly, or via one of the bases below)."""

    async def _score(self, case: Case, output: Any) -> list[Score]:
        """The judge's main scoring routine — the concrete work behind
        `EvaluatorPort.evaluate()`, run inside that method's shared error
        boundary. One template shared by all five judges: build the prompt
        (`_build_prompt`, which may return None to skip the LLM call when
        there's nothing to score), invoke the judge with retries, parse the
        raw response, then delegate to `_build_scores` — the single scoring
        hook each judge implements for its own response shape.
        """
        prompt = self._build_prompt(case, output)
        if prompt is not None:
            response = await self.invoke_with_retry(prompt)
            parsed = self._parse_json_markdown(response.parsed)
        else:
            parsed: dict = {}

        return self._build_scores(parsed)


class ThemeComparisonJudgeEvaluator(LLMJudgeEvaluator):
    """Base for judges that compare two theme lists in one LLM call. Retrieves
    the case-side themes from the `Case` field named by `ground_truth_attr`
    (`"expected_output"` by default) and the output-side from
    `output["themes"]`, orders the pair via `_topic_order`, and passes them to
    `prompt_fn` under the names in `first_kwarg`/`second_kwarg`. Scores the
    parsed response by extracting one named numeric key per metric.
    """

    first_kwarg: str = "topic_list_1"
    second_kwarg: str = "topic_list_2"

    #: Name of the `Case` field holding this evaluator's case-side
    #: (ground-truth / pre-transform) themes.
    ground_truth_attr: str = "expected_output"

    def _topic_order(self, case_themes: Any, output_themes: Any) -> tuple[Any, Any]:
        """Order the two retrieved theme lists into (topic_list_1,
        topic_list_2). Defaults to case-side first, output-side second;
        subclasses may override to swap without touching retrieval."""
        return case_themes, output_themes

    def _build_prompt(self, case: Case, output: Any) -> str:
        """Retrieve the two theme lists — case-side from the `ground_truth_attr`
        field, output-side from `output["themes"]` — order them via
        `_topic_order`, optionally shuffle, and pass them to `prompt_fn` under
        its two keyword-argument names."""
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
        """Extract one Score per name in `metric_names` directly from the
        parsed response, reading each metric's numeric value and its
        `{metric}_reasoning` comment."""
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
    """Theme-comparison judge whose prompt asks for a per-theme
    STRONG/PARTIAL/NO decision rather than named numeric scores. Maps those
    decisions to 0-5, averages them into a single metric, and builds an
    enriched comment; subclasses set `threshold_label` for the comment summary.
    """

    #: Phrase used in the comment summary, e.g. "themes below threshold".
    threshold_label: str = ""

    def _build_scores(self, parsed: dict) -> list[Score]:
        """Map the parsed per-theme STRONG/PARTIAL/NO decisions to a single
        averaged 0-5 metric with an enriched comment — overriding the
        numeric-key extraction inherited from `ThemeComparisonJudgeEvaluator`."""
        result = self._decision_score(parsed)
        metric_name = self.metric_names[0]
        comment = self._build_comment(result)
        return [Score(metric_name, round(result["average"], 2), comment)]

    def _decision_score(self, parsed: dict) -> dict[str, Any]:
        """Turn a parsed STRONG/PARTIAL/NO ternary-decision response into
        numeric scores plus per-topic details.

        Args:
            parsed: The judge's response, already run through `_parse_json_markdown`.

        Returns:
            Dict with scores, average, threshold counts, and per-topic details.
        """
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
        """Build an enriched comment from decision-scored evaluation details:
        a `n_below_threshold/n_total {threshold_label}` summary, then one line
        per theme — unless the response was in the legacy numeric format, which
        carries no per-theme decisions and so gets the summary alone."""
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
