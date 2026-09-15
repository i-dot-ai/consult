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

import types

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


ALL_JUDGE_CLASSES = [
    GroundednessEvaluator,
    CoverageEvaluator,
    CondensationQualityEvaluator,
    RefinementQualityEvaluator,
    TitleSpecificityEvaluator,
]


@pytest.mark.parametrize("cls", ALL_JUDGE_CLASSES)
def test_judge_is_evaluator_port(cls):
    assert isinstance(cls(_FakeJudge()), EvaluatorPort)


class TestDecisionScoredJudges:
    """GroundednessEvaluator / CoverageEvaluator — the STRONG/PARTIAL/NO
    ternary path (`_decision_score` / `_build_comment`)."""

    async def test_maps_ternary_decisions_to_scores(self):
        judge = _FakeJudge(
            '{"evaluations": {'
            '"A": {"decision": "STRONG", "matched_to": "x", "reasoning": "r"},'
            '"B": {"decision": "PARTIAL", "matched_to": "y", "reasoning": "r"},'
            '"C": {"decision": "NO", "reasoning": "r"}}}'
        )
        case = make_case(expected_output={"themes": []})

        scores = await GroundednessEvaluator(judge).evaluate(case, {"themes": []})

        # STRONG=5, PARTIAL=3, NO=0 -> mean 8/3 = 2.67; only NO (0) is below
        # the groundedness threshold of 3.
        assert scores[0].name == "groundedness"
        assert scores[0].value == round(8 / 3, 2)
        assert "1/3 themes below threshold" in scores[0].comment

    async def test_empty_evaluations_scores_zero(self):
        judge = _FakeJudge('{"evaluations": {}}')
        case = make_case(expected_output={"themes": []})

        scores = await GroundednessEvaluator(judge).evaluate(case, {"themes": []})

        assert scores[0].value == 0.0
        assert "0/0 themes below threshold" in scores[0].comment

    async def test_legacy_numeric_format_still_scored(self):
        # Backwards-compat: a bare 0-5 number per theme instead of a decision dict.
        judge = _FakeJudge('{"evaluations": {"A": 4, "B": 2}}')
        case = make_case(expected_output={"themes": []})

        scores = await GroundednessEvaluator(judge).evaluate(case, {"themes": []})

        # mean(4, 2) = 3.0; one theme (2) below threshold. Legacy details carry
        # no per-theme decision lines, so the comment is just the summary.
        assert scores[0].value == 3.0
        assert scores[0].comment == "1/2 themes below threshold"

    async def test_evaluations_key_optional(self):
        # No "evaluations" wrapper — `_decision_score` falls back to the top-level dict.
        judge = _FakeJudge(
            '{"A": {"decision": "STRONG", "matched_to": "x", "reasoning": "r"}}'
        )
        case = make_case(expected_output={"themes": []})

        scores = await GroundednessEvaluator(judge).evaluate(case, {"themes": []})

        assert scores[0].value == 5.0

    async def test_groundedness_comment_wording_and_detail_lines(self):
        judge = _FakeJudge(
            '{"evaluations": {'
            '"A": {"decision": "STRONG", "matched_to": "x", "reasoning": "clear"},'
            '"B": {"decision": "NO", "reasoning": "missing"}}}'
        )
        case = make_case(expected_output={"themes": []})

        scores = await GroundednessEvaluator(judge).evaluate(case, {"themes": []})

        comment = scores[0].comment
        assert comment.startswith("1/2 themes below threshold")
        assert "STRONG: A → x — clear" in comment
        assert "NO: B (no match) — missing" in comment

    async def test_coverage_uses_not_captured_wording(self):
        judge = _FakeJudge(
            '{"evaluations": {"A": {"decision": "NO", "reasoning": "r"}}}'
        )
        case = make_case(expected_output={"themes": []})

        scores = await CoverageEvaluator(judge).evaluate(case, {"themes": []})

        assert scores[0].name == "coverage"
        assert "1/1 themes not captured" in scores[0].comment

    async def test_groundedness_scores_output_against_expected(self):
        """Wiring: GroundednessEvaluator._topic_order swaps, so output themes
        become topic_list_1 (scored first) and expected themes topic_list_2."""
        judge = _FakeJudge('{"evaluations": {}}')
        case = make_case(expected_output={"themes": [{"topic_label": "EXPECTED_ONLY"}]})

        await GroundednessEvaluator(judge).evaluate(
            case, {"themes": [{"topic_label": "OUTPUT_ONLY"}]}
        )

        prompt = judge.prompts[0]
        assert prompt.index("OUTPUT_ONLY") < prompt.index("EXPECTED_ONLY")

    async def test_coverage_scores_expected_against_output(self):
        """Wiring: CoverageEvaluator keeps the default order, so expected
        themes are topic_list_1 and output themes topic_list_2 (reverse of
        groundedness — same two lists, opposite direction)."""
        judge = _FakeJudge('{"evaluations": {}}')
        case = make_case(expected_output={"themes": [{"topic_label": "EXPECTED_ONLY"}]})

        await CoverageEvaluator(judge).evaluate(
            case, {"themes": [{"topic_label": "OUTPUT_ONLY"}]}
        )

        prompt = judge.prompts[0]
        assert prompt.index("EXPECTED_ONLY") < prompt.index("OUTPUT_ONLY")


class TestNumericKeyJudges:
    """CondensationQualityEvaluator / RefinementQualityEvaluator — the
    numeric-key path (`ThemeComparisonJudgeEvaluator._build_scores`)."""

    async def test_condensation_extracts_named_metrics(self):
        judge = _FakeJudge(
            '{"compression_quality": 4, "compression_quality_reasoning": "tight",'
            ' "information_retention": 5, "information_retention_reasoning": "kept"}'
        )
        case = make_case(inputs={"themes": []})

        scores = await CondensationQualityEvaluator(judge).evaluate(
            case, {"themes": []}
        )

        assert scores == [
            Score("compression_quality", 4.0, "tight"),
            Score("information_retention", 5.0, "kept"),
        ]

    async def test_missing_metric_defaults_to_zero(self):
        # information_retention absent from the response.
        judge = _FakeJudge(
            '{"compression_quality": 4, "compression_quality_reasoning": "tight"}'
        )
        case = make_case(inputs={"themes": []})

        scores = await CondensationQualityEvaluator(judge).evaluate(
            case, {"themes": []}
        )

        assert scores[1] == Score("information_retention", 0.0, "")

    async def test_refinement_returns_all_four_metrics(self):
        judge = _FakeJudge(
            '{"information_retention": 5, "response_references": 4,'
            ' "distinctiveness": 3, "fluency": 2}'
        )
        case = make_case(inputs={"themes": []})

        scores = await RefinementQualityEvaluator(judge).evaluate(case, {"themes": []})

        assert [s.name for s in scores] == [
            "information_retention",
            "response_references",
            "distinctiveness",
            "fluency",
        ]
        assert [s.value for s in scores] == [5.0, 4.0, 3.0, 2.0]

    async def test_reads_case_themes_from_inputs(self):
        """Wiring: condensation/refinement have no ground truth
        (expected_output is None), so case-side themes come from
        `case.inputs["themes"]` and land as `original_topics` (before the
        output's `condensed_topics`) in the prompt."""
        judge = _FakeJudge("{}")
        case = make_case(inputs={"themes": [{"topic_label": "INPUT_ONLY"}]})

        await CondensationQualityEvaluator(judge).evaluate(
            case, {"themes": [{"topic_label": "OUTPUT_ONLY"}]}
        )

        prompt = judge.prompts[0]
        assert prompt.index("INPUT_ONLY") < prompt.index("OUTPUT_ONLY")


class TestTitleSpecificityEvaluator:
    async def test_counts_specific_vs_vague(self):
        judge = _FakeJudge(
            '{"evaluations": {'
            '"Housing costs in cities": {"decision": "SPECIFIC"},'
            '"Stuff": {"decision": "VAGUE"}}}'
        )
        output = {
            "themes": [
                {"topic_label": "Housing costs in cities"},
                {"topic_label": "Stuff"},
            ]
        }

        scores = await TitleSpecificityEvaluator(judge).evaluate(make_case(), output)

        assert scores[0].name == "specificity"
        assert scores[0].value == 0.5
        assert scores[0].comment == "1/2 titles specific\nVague: Stuff"

    async def test_no_titles_skips_llm_call(self):
        judge = _FakeJudge()

        scores = await TitleSpecificityEvaluator(judge).evaluate(
            make_case(), {"themes": []}
        )

        # _build_prompt returns None when there are no titles -> the LLM is
        # never invoked, and _build_scores({}) yields the empty-case comment.
        assert judge.prompts == []
        assert scores == [Score("specificity", 0.0, "0/0 titles specific")]


class TestErrorBoundary:
    """A failing judge should degrade to one zero-Score per metric name via
    `EvaluatorPort.evaluate()`'s shared try/except, not raise."""

    @pytest.mark.parametrize(
        "cls, expected_metrics",
        [
            (GroundednessEvaluator, ("groundedness",)),
            (CoverageEvaluator, ("coverage",)),
            (
                CondensationQualityEvaluator,
                ("compression_quality", "information_retention"),
            ),
            (
                RefinementQualityEvaluator,
                (
                    "information_retention",
                    "response_references",
                    "distinctiveness",
                    "fluency",
                ),
            ),
            (TitleSpecificityEvaluator, ("specificity",)),
        ],
    )
    async def test_judge_failure_degrades_to_zero_scores(self, cls, expected_metrics):
        # Provide themes on every field so each evaluator builds a real prompt
        # and actually reaches the (raising) LLM call.
        themes = {"themes": [{"topic_label": "t"}]}
        case = make_case(inputs=themes, expected_output=themes)

        scores = await cls(_RaisingJudge()).evaluate(case, themes)

        assert [s.name for s in scores] == list(expected_metrics)
        assert all(s.value == 0.0 for s in scores)
        assert all(s.comment.startswith("Error:") for s in scores)


@pytest.mark.parametrize(
    "parsed",
    [
        '{"compression_quality": 4, "compression_quality_reasoning": "r",'
        ' "information_retention": 5, "information_retention_reasoning": "r"}',
        '```json\n{"compression_quality": 4, "compression_quality_reasoning": "r",'
        ' "information_retention": 5, "information_retention_reasoning": "r"}\n```',
    ],
    ids=["bare", "fenced"],
)
async def test_parses_bare_and_fenced_json(parsed):
    """`_parse_json_markdown` handles both a bare JSON string and one wrapped
    in a ```json code fence."""
    case = make_case(inputs={"themes": []})

    scores = await CondensationQualityEvaluator(_FakeJudge(parsed)).evaluate(
        case, {"themes": []}
    )

    assert [s.value for s in scores] == [4.0, 5.0]
