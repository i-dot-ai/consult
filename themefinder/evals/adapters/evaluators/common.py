"""Shared LLM-judge machinery: `LLMJudgeEvaluator` and `ThemeComparisonJudgeEvaluator`.

Moved from `evaluators.py` (behaviour-preserving, not byte-identical — the
old factory closures and module-level helper functions become methods on
this class hierarchy). The five LLM-judge `EvaluatorPort` subclasses live in
their own sibling files: groundedness.py, coverage.py, title_specificity.py,
condensation_quality.py, refinement_quality.py.

`LLMJudgeEvaluator._score()` is one shared template for all five judges:
build a prompt (`_build_prompt`, subclass hook — may return None to skip the
LLM call entirely when there's nothing to evaluate), invoke the judge,
*always* parse the raw response via `_parse_json_markdown`, then either run
the STRONG/PARTIAL/NO ternary post-processing (`_decision_score`/
`_build_comment`, only when `decision_scored` is True) or hand the parsed
dict to the subclass's own `_build_scores` hook. `shuffle` is a second
opt-in class property, read by whichever subclass's `_build_prompt` wants it
(today, only `ThemeComparisonJudgeEvaluator`'s). The error boundary around
all of this — catch, log, zero-score fallback — lives on `EvaluatorPort.evaluate()`,
not here.
"""

import json
import logging
import random
import re
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
    """Base for the five LLM-as-judge evaluators — carries the judge LLM,
    the shared retry/parsing plumbing, and the one `_score()` template
    every one of them runs through.

    Subclasses set:
    - `prompt_fn`: the prompts.py builder function, as `staticmethod(...)`.
    - `metric_names`: tuple of Score names this evaluator produces — a
      1-tuple for single-metric evaluators, used both for the decision-scored
      path's one Score and for `EvaluatorPort.evaluate()`'s error-path
      zero-score fallback list.
    - `shuffle` (default False): whether `_build_prompt` should shuffle its
      theme-list inputs before prompting.
    - `decision_scored` (default False): whether `_score()` should run the
      STRONG/PARTIAL/NO ternary post-processing on the parsed response
      (`_decision_score`/`_build_comment`) instead of calling the subclass's
      own `_build_scores`.

    And implement:
    - `_build_prompt(case, output) -> str | None`: build the judge prompt, or
      return None to skip the LLM call entirely (nothing to evaluate).
    - `_build_scores(parsed) -> list[Score]`: only called when
      `decision_scored` is False — turn the parsed response into Scores.
    """

    shuffle: bool = False
    decision_scored: bool = False

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

    def _decision_score(self, parsed: dict) -> dict[str, Any]:
        """Post-process an already-parsed STRONG/PARTIAL/NO ternary-decision response.

        Only called by `_score()` when `decision_scored = True`. Extracts
        per-topic evaluations and maps decisions to numeric scores.

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

    @staticmethod
    def _build_comment(result: dict[str, Any], metric_name: str) -> str:
        """Build an enriched comment string from decision-scored evaluation details.

        Only called by `_score()` when `decision_scored = True`.

        Args:
            result: Parsed evaluation result from _decision_score.
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

    def _build_prompt(self, case: Case, output: Any) -> str | None:
        """Build the judge prompt, or None to skip the LLM call entirely
        (nothing to evaluate). Every subclass implements this."""
        raise NotImplementedError

    def _build_scores(self, parsed: dict) -> list[Score]:
        """Turn the parsed response into Scores. Only called when
        `decision_scored` is False — decision-scored evaluators use
        `_decision_score`/`_build_comment` instead."""
        raise NotImplementedError

    async def _score(self, case: Case, output: Any) -> list[Score]:
        prompt = self._build_prompt(case, output)
        if prompt is None:
            parsed: dict = {}
        else:
            response = await self.invoke_with_retry(prompt)
            parsed = self._parse_json_markdown(response.parsed)

        if self.decision_scored:
            result = self._decision_score(parsed)
            metric_name = self.metric_names[0]
            comment = self._build_comment(result, metric_name)
            return [Score(metric_name, round(result["average"], 2), comment)]

        return self._build_scores(parsed)


class ThemeComparisonJudgeEvaluator(LLMJudgeEvaluator):
    """Base for any evaluator whose judge prompt compares two theme lists in
    one LLM call: groundedness/coverage (via `generation_eval_prompt`,
    ternary decision-scored) and condensation/refinement quality (via their
    own prompts, direct multi-key numeric extraction). Subclasses implement
    `_topic_lists` — no boolean "reverse" flag; each subclass just states its
    own (topic_list_1, topic_list_2) directly — and set `prompt_fn` plus
    `first_kwarg`/`second_kwarg` naming the two keyword arguments that
    particular prompt function expects (default `"topic_list_1"`/
    `"topic_list_2"`, matching `generation_eval_prompt`; condensation/
    refinement override these to their own prompts' argument names).
    `shuffle`/`decision_scored` default to `LLMJudgeEvaluator`'s `False` here
    too — groundedness/coverage turn both on, condensation/refinement turn
    neither on (no shuffling today, and they extract named numeric keys
    directly rather than ternary-scoring, via this class's shared
    `_build_scores` below).
    """

    first_kwarg: str = "topic_list_1"
    second_kwarg: str = "topic_list_2"

    def _topic_lists(self, case: Case, output: Any) -> tuple[Any, Any]:
        raise NotImplementedError

    def _build_prompt(self, case: Case, output: Any) -> str:
        topic_list_1, topic_list_2 = self._topic_lists(case, output)
        if self.shuffle:
            topic_list_1 = self._shuffle_themes(topic_list_1)
            topic_list_2 = self._shuffle_themes(topic_list_2)
        return self.prompt_fn(
            **{self.first_kwarg: topic_list_1, self.second_kwarg: topic_list_2}
        )

    def _build_scores(self, parsed: dict) -> list[Score]:
        """Default for the non-decision-scored subclasses (condensation,
        refinement): extract one Score per name in `metric_names` directly
        from the parsed response, whose judge prompts return named numeric
        keys plus a `{metric}_reasoning` string rather than a ternary
        per-topic decision. Both current subclasses share this verbatim, so
        it lives here instead of being copy-pasted onto each."""
        return [
            Score(
                metric,
                round(float(parsed.get(metric, 0)), 2),
                parsed.get(f"{metric}_reasoning", ""),
            )
            for metric in self.metric_names
        ]
