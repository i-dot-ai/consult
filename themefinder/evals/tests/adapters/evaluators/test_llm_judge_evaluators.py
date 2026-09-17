"""Tests for the five LLM-as-a-judge evaluator adapters: GroundednessEvaluator,
CoverageEvaluator (decision-scored), CondensationQualityEvaluator,
RefinementQualityEvaluator (numeric-key), and TitleSpecificityEvaluator
(bespoke ratio).

These test each evaluator's *own* logic — prompt wiring, response parsing,
score mapping, comment formatting, and the skip/error paths — using a fake
judge LLM. We deliberately do NOT exercise the real LLM, the OpenAI client, or
tenacity's retry mechanics: those are the library's job (same reasoning as the
deterministic tests not re-testing cosine-similarity math). The prompt builder
functions in prompts.py are pure `str.format()` calls, so we use the real ones
and assert on the emitted prompt string for wiring checks.
"""

import json
import types
from collections import namedtuple

import pytest
from adapters.evaluators.base import EvaluatorPort
from adapters.evaluators.condensation_quality import CondensationQualityEvaluator
from adapters.evaluators.coverage import CoverageEvaluator
from adapters.evaluators.groundedness import GroundednessEvaluator
from adapters.evaluators.refinement_quality import RefinementQualityEvaluator
from adapters.evaluators.title_specificity import TitleSpecificityEvaluator
from conftest import make_case
from eval_types import Score


class _FakeJudge:
    """Stands in for the injected judge LLM. Records the prompts it was asked
    to score (for wiring assertions) and returns a canned `.parsed` JSON
    string — exactly what themefinder.llm.LLMResponse exposes, and all that
    `LLMJudgeEvaluator._score()` consumes. No openai client or real model
    involved: we test the evaluator, not the LLM.
    """

    def __init__(self, parsed: str = "{}"):
        self.parsed = parsed
        self.prompts: list[str] = []

    async def ainvoke(self, prompt: str):
        self.prompts.append(prompt)
        return types.SimpleNamespace(parsed=self.parsed)


class _RaisingJudge:
    """A judge whose `ainvoke` raises — to exercise `EvaluatorPort.evaluate()`'s
    shared error boundary. A plain Exception is non-transient, so tenacity
    reraises it immediately (no retry sleeps), keeping the test fast."""

    async def ainvoke(self, prompt: str):
        raise RuntimeError("boom")


class _JudgeContractTests:
    """The contract every LLM-judge evaluator inherits from EvaluatorPort /
    LLMJudgeEvaluator — port conformance and the shared error boundary. Run
    against each concrete judge by subclassing rather than duplicated per file:
    each per-evaluator test class subclasses this and provides `evaluator_cls`
    (a class attribute, or set on the instance by a fixture for the parametrised
    judges). The metric names the contract checks are read from that evaluator's
    own `metric_names`, so there's a single source of truth to follow."""

    evaluator_cls: type

    async def _evaluate(self, judge, *, output=None, **case_kwargs):
        """Run this class's evaluator against a case and return the scores — the
        single entry point every test drives the evaluator through. With no
        arguments the case and output carry themes on every field, so any judge
        reaches its LLM call whichever field it reads them from. Wiring and
        skip-path tests forward their own make_case kwargs (`inputs` /
        `expected_output`) and `output` to place marker or empty themes, then
        inspect the recorded `judge.prompts` afterwards."""
        themes = {"themes": {"t": "desc"}}
        if not case_kwargs:
            case_kwargs = {"inputs": themes, "expected_output": themes}
        case = make_case(**case_kwargs)
        return await self.evaluator_cls(judge).evaluate(
            case, themes if output is None else output
        )

    def test_is_evaluator_port(self):
        assert isinstance(self.evaluator_cls(_FakeJudge()), EvaluatorPort)

    async def test_judge_failure_degrades_to_zero_scores(self):
        """A failing judge degrades to one zero-Score per metric name via
        `EvaluatorPort.evaluate()`'s shared try/except, rather than raising."""
        scores = await self._evaluate(_RaisingJudge())

        assert [s.name for s in scores] == list(self.evaluator_cls.metric_names)
        assert all(s.value == 0.0 for s in scores)
        assert all(s.comment.startswith("Error:") for s in scores)


#: The two decision-scored judges, which share all their scoring machinery
#: (STRONG/PARTIAL/NO → 5/3/0, averaging, comment building) via
#: `DecisionScoredComparisonJudge` and differ only in their comment summary
#: phrase and their topic order (groundedness scores output→expected; coverage
#: scores expected→output, so the marker expected to appear *first* in the
#: prompt differs). The metric name comes from each evaluator's own
#: `metric_names`, so it isn't duplicated here.
_DecisionJudge = namedtuple(
    "_DecisionJudge", "cls summary_phrase first_marker second_marker"
)

DECISION_SCORED_JUDGES = [
    pytest.param(
        _DecisionJudge(
            GroundednessEvaluator,
            "themes below threshold",
            "OUTPUT_ONLY",
            "EXPECTED_ONLY",
        ),
        id="groundedness",
    ),
    pytest.param(
        _DecisionJudge(
            CoverageEvaluator,
            "themes not captured",
            "EXPECTED_ONLY",
            "OUTPUT_ONLY",
        ),
        id="coverage",
    ),
]


@pytest.mark.parametrize("judge_cfg", DECISION_SCORED_JUDGES)
class TestDecisionScoredJudges(_JudgeContractTests):
    """GroundednessEvaluator and CoverageEvaluator — one set of tests over both.
    They share the STRONG/PARTIAL/NO ternary machinery inherited from
    `DecisionScoredComparisonJudge` (`_decision_score` / `_build_comment`) and
    differ only in their expected outcomes: metric name, comment summary phrase,
    and topic order. An autouse fixture unpacks the parametrised `judge_cfg`
    onto the instance, so each test (including the inherited contract tests,
    which run once per judge) reads `self.evaluator_cls`, `self.metric`, etc."""

    @pytest.fixture(autouse=True)
    def _setup(self, judge_cfg):
        self.evaluator_cls = judge_cfg.cls
        self.metric = judge_cfg.cls.metric_names[0]
        self.summary_phrase = judge_cfg.summary_phrase
        self.first_marker = judge_cfg.first_marker
        self.second_marker = judge_cfg.second_marker

    async def test_maps_ternary_decisions_to_scores(self):
        judge = _FakeJudge(
            '{"evaluations": {'
            '"A": {"decision": "STRONG", "matched_to": "x", "reasoning": "r"},'
            '"B": {"decision": "PARTIAL", "matched_to": "y", "reasoning": "r"},'
            '"C": {"decision": "NO", "reasoning": "r"}}}'
        )
        scores = await self._evaluate(judge)

        # STRONG=5, PARTIAL=3, NO=0 -> mean 8/3 = 2.67; only NO (0) is below
        # the threshold of 3.
        assert scores[0].name == self.metric
        assert scores[0].value == round(8 / 3, 2)
        assert f"1/3 {self.summary_phrase}" in scores[0].comment

    async def test_empty_evaluations_scores_zero(self):
        judge = _FakeJudge('{"evaluations": {}}')
        scores = await self._evaluate(judge)

        assert scores[0].value == 0.0
        assert f"0/0 {self.summary_phrase}" in scores[0].comment

    async def test_legacy_numeric_format_still_scored(self):
        # Backwards-compat: a bare 0-5 number per theme instead of a decision dict.
        judge = _FakeJudge('{"evaluations": {"A": 4, "B": 2}}')
        scores = await self._evaluate(judge)

        # mean(4, 2) = 3.0; one theme (2) below threshold. Legacy details carry
        # no per-theme decision lines, so the comment is just the summary.
        assert scores[0].value == 3.0
        assert scores[0].comment == f"1/2 {self.summary_phrase}"

    async def test_evaluations_key_optional(self):
        # No "evaluations" wrapper — `_decision_score` falls back to the top-level dict.
        judge = _FakeJudge(
            '{"A": {"decision": "STRONG", "matched_to": "x", "reasoning": "r"}}'
        )
        scores = await self._evaluate(judge)

        assert scores[0].value == 5.0

    async def test_comment_wording_and_detail_lines(self):
        judge = _FakeJudge(
            '{"evaluations": {'
            '"A": {"decision": "STRONG", "matched_to": "x", "reasoning": "clear"},'
            '"B": {"decision": "NO", "reasoning": "missing"}}}'
        )
        scores = await self._evaluate(judge)

        comment = scores[0].comment
        assert comment.startswith(f"1/2 {self.summary_phrase}")
        assert "STRONG: A → x — clear" in comment
        assert "NO: B (no match) — missing" in comment

    async def test_topic_order_wiring(self):
        """`_topic_order` decides which theme list is scored first: groundedness
        swaps (output first), coverage keeps the default (expected first). Each
        judge's `first_marker` is the one expected earliest in the prompt."""
        judge = _FakeJudge('{"evaluations": {}}')

        await self._evaluate(
            judge,
            expected_output={"themes": {"EXPECTED_ONLY": "desc"}},
            output={"themes": {"OUTPUT_ONLY": "desc"}},
        )

        prompt = judge.prompts[0]
        assert prompt.index(self.first_marker) < prompt.index(self.second_marker)


class _NumericKeyJudgeTests(_JudgeContractTests):
    """Shared contract for the numeric-key judges (condensation, refinement),
    which both extract one numeric value plus a `{metric}_reasoning` string per
    metric via `ThemeComparisonJudgeEvaluator._build_scores` — the *same*
    inherited method. Rather than test that method twice and let the two copies
    drift, both classes inherit these tests and differ only in their
    `evaluator_cls` / `metric_names`. Responses and expected Scores are built
    from the evaluator's own `metric_names`, so nothing is hard-coded."""

    #: Reasoning strings zipped onto the metrics (one per metric) — arbitrary,
    #: just needs enough entries to cover the widest evaluator's metric_names.
    options = ["tight", "loose", "kept", "lost"]

    async def test_extracts_named_metrics(self):
        # Build the judge response and the expected Scores from the evaluator's
        # own metric_names, so nothing is hard-coded and the test follows along
        # if the evaluator's metrics change.
        expected_scores = range(len(self.metric_names))
        expected_reasonings = self.options[: len(self.metric_names)]
        response = {}
        for metric, score, reasoning in zip(
            self.metric_names, expected_scores, expected_reasonings
        ):
            response[metric] = score
            response[f"{metric}_reasoning"] = reasoning
        judge = _FakeJudge(json.dumps(response))

        scores = await self._evaluate(judge)

        assert scores == [
            Score(metric, float(score), reasoning)
            for metric, score, reasoning in zip(
                self.metric_names, expected_scores, expected_reasonings
            )
        ]

    async def test_missing_metric_defaults_to_zero(self):
        # Only the first metric is present; the second is absent from the
        # response and must fall back to 0.0 with an empty comment. Skip
        # for evaluators with only one metric.
        if len(self.metric_names) == 1:
            pytest.skip("single-metric evaluators have no topic order to test")

        present, missing = self.metric_names[0], self.metric_names[1]
        judge = _FakeJudge(json.dumps({present: 4, f"{present}_reasoning": "tight"}))

        scores = await self._evaluate(judge)

        assert scores[1] == Score(missing, 0.0, "")

    async def test_parses_fenced_json(self):
        """`_parse_json_markdown` strips a ```json code fence before parsing —
        the one parsing branch the other tests don't cover (they all feed bare
        JSON), and one real judges routinely trigger."""
        first = self.metric_names[0]
        body = json.dumps({first: 4, f"{first}_reasoning": "r"})
        judge = _FakeJudge(f"```json\n{body}\n```")

        scores = await self._evaluate(judge)

        assert scores[0] == Score(first, 4.0, "r")


class TestCondensationQualityEvaluator(_NumericKeyJudgeTests):
    """CondensationQualityEvaluator — the numeric-key path
    (`ThemeComparisonJudgeEvaluator._build_scores`), reading case-side themes
    from `case.inputs` since there's no ground-truth `expected_output`. Inherits
    the numeric-key contract; adds the input-side wiring check below."""

    evaluator_cls = CondensationQualityEvaluator
    metric_names = evaluator_cls.metric_names

    async def test_reads_case_themes_from_inputs(self):
        """Wiring: condensation/refinement have no ground truth
        (expected_output is None), so case-side themes come from
        `case.inputs["themes"]` and land as `original_topics` (before the
        output's `condensed_topics`) in the prompt."""
        judge = _FakeJudge("{}")

        await self._evaluate(
            judge,
            inputs={"themes": {"INPUT_ONLY": "desc"}},
            output={"themes": {"OUTPUT_ONLY": "desc"}},
        )

        prompt = judge.prompts[0]
        assert prompt.index("INPUT_ONLY") < prompt.index("OUTPUT_ONLY")


class TestRefinementQualityEvaluator(_NumericKeyJudgeTests):
    """RefinementQualityEvaluator — the numeric-key path over its own four
    metrics (information_retention, response_references, distinctiveness,
    fluency). Same inherited `_build_scores` as condensation, so it inherits the
    full numeric-key contract and only pins its own `metric_names`."""

    evaluator_cls = RefinementQualityEvaluator
    metric_names = evaluator_cls.metric_names


class TestTitleSpecificityEvaluator(_JudgeContractTests):
    """TitleSpecificityEvaluator — its bespoke SPECIFIC/VAGUE ratio path,
    scoring `output["themes"]`'s titles alone and skipping the LLM call when
    there are no titles."""

    evaluator_cls = TitleSpecificityEvaluator

    async def test_counts_specific_vs_vague(self):
        judge = _FakeJudge(
            '{"evaluations": {'
            '"Housing costs in cities": {"decision": "SPECIFIC"},'
            '"Stuff": {"decision": "VAGUE"}}}'
        )
        output = {"themes": {"Housing costs in cities": "desc", "Stuff": "desc"}}

        scores = await self._evaluate(judge, output=output)

        assert scores[0].name == "specificity"
        assert scores[0].value == 0.5
        assert scores[0].comment == "1/2 titles specific\nVague: Stuff"

    async def test_no_titles_skips_llm_call(self):
        judge = _FakeJudge()

        scores = await self._evaluate(judge, output={"themes": {}})

        # _build_prompt returns None when there are no titles -> the LLM is
        # never invoked, and _build_scores({}) yields the empty-case comment.
        assert judge.prompts == []
        assert scores == [Score("specificity", 0.0, "0/0 titles specific")]
