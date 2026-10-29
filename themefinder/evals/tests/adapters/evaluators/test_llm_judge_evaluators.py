"""Tests for LLM-as-a-judge evaluator adapters."""

import json
from collections import namedtuple

import pytest
from adapters.evaluators.clarity_evaluator import ClarityEvaluator
from adapters.evaluators.condensation_quality_evaluator import (
    CondensationQualityEvaluator,
)
from adapters.evaluators.coverage_evaluator import CoverageEvaluator
from adapters.evaluators.ground_information_evaluator import (
    GroundednessInformationRetentionEvaluator,
)
from adapters.evaluators.groundedness_evaluator import GroundednessEvaluator
from adapters.evaluators.refinement_quality_evaluator import RefinementQualityEvaluator
from adapters.evaluators.title_specificity_evaluator import TitleSpecificityEvaluator
from conftest import _themes, make_case
from eval_types import Score
from fakes import FakeJudge, SequenceFakeJudge


class _RaisingJudge:
    """A judge whose `ainvoke` raises"""

    async def ainvoke(self, prompt: str):
        raise RuntimeError("boom")


class _JudgeContractTests:
    """Base class testing the contract every LLM-judge evaluator inherits from EvaluatorPort"""

    evaluator_cls: type

    async def _evaluate(self, judge, *, output=None, **case_kwargs):
        """Helper function to run the evaluator under test with a fake judge and a simple case."""
        themes = {"themes": _themes("t")}
        if not case_kwargs:
            case_kwargs = {"inputs": themes, "expected_output": themes}
        case = make_case(**case_kwargs)
        return await self.evaluator_cls(judge).evaluate(
            case, themes if output is None else output
        )

    async def test_judge_failure_degrades_to_zero_scores(self):
        """A failing judge degrades to one zero Score per metric name, not a raise."""
        scores = await self._evaluate(_RaisingJudge())

        assert [s.name for s in scores] == list(self.evaluator_cls.metric_names)
        assert all(s.value == 0.0 for s in scores)
        assert all(s.comment.startswith("Error:") for s in scores)


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
    """GroundednessEvaluator and CoverageEvaluator — one set of tests over both."""

    @pytest.fixture(autouse=True)
    def _setup(self, judge_cfg):
        self.evaluator_cls = judge_cfg.cls
        self.metric = judge_cfg.cls.metric_names[0]
        self.summary_phrase = judge_cfg.summary_phrase
        self.first_marker = judge_cfg.first_marker
        self.second_marker = judge_cfg.second_marker

    async def test_maps_ternary_decisions_to_scores(self):
        """STRONG/PARTIAL/NO decisions map to 5/3/0 and average into the metric score."""
        judge = FakeJudge(
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
        """An empty evaluations dict (no themes) yields a 0.0 score and a comment"""
        judge = FakeJudge('{"evaluations": {}}')
        scores = await self._evaluate(judge)

        assert scores[0].value == 0.0
        assert f"0/0 {self.summary_phrase}" in scores[0].comment

    async def test_legacy_numeric_format_still_scored(self):
        """Legacy bare 0-5 numbers per theme are still averaged into the score."""
        judge = FakeJudge('{"evaluations": {"A": 4, "B": 2}}')
        scores = await self._evaluate(judge)

        # mean(4, 2) = 3.0; one theme (2) below threshold. Legacy details carry
        # no per-theme decision lines, so the comment is just the summary.
        assert scores[0].value == 3.0
        assert scores[0].comment == f"1/2 {self.summary_phrase}"

    async def test_evaluations_key_optional(self):
        """With no `evaluations` wrapper, scoring falls back to the top-level dict."""
        judge = FakeJudge(
            '{"A": {"decision": "STRONG", "matched_to": "x", "reasoning": "r"}}'
        )
        scores = await self._evaluate(judge)

        assert scores[0].value == 5.0

    async def test_comment_wording_and_detail_lines(self):
        """The comment carries the threshold summary plus one detail line per theme."""
        judge = FakeJudge(
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
        """`_topic_order` sets which theme list appears first in the prompt per judge."""
        judge = FakeJudge('{"evaluations": {}}')

        await self._evaluate(
            judge,
            expected_output={"themes": _themes("EXPECTED_ONLY")},
            output={"themes": _themes("OUTPUT_ONLY")},
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
    options = ("tight", "loose", "kept", "lost")

    async def test_extracts_named_metrics(self):
        """Each metric and its `{metric}_reasoning` are extracted into a named Score."""
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
        judge = FakeJudge(json.dumps(response))

        scores = await self._evaluate(judge)

        assert scores == [
            Score(metric, float(score), reasoning)
            for metric, score, reasoning in zip(
                self.metric_names, expected_scores, expected_reasonings
            )
        ]

    async def test_missing_metric_defaults_to_zero(self):
        """A metric absent from the response falls back to a 0.0 Score with empty comment."""
        # Only the first metric is present; the second is absent from the
        # response and must fall back to 0.0 with an empty comment. Skip
        # for evaluators with only one metric.
        if len(self.metric_names) == 1:
            pytest.skip("single-metric evaluators have no topic order to test")

        present, missing = self.metric_names[0], self.metric_names[1]
        judge = FakeJudge(json.dumps({present: 4, f"{present}_reasoning": "tight"}))

        scores = await self._evaluate(judge)

        assert scores[1] == Score(missing, 0.0, "")

    async def test_parses_fenced_json(self):
        """`_parse_json_markdown` strips a ```json code fence before parsing the response."""
        first = self.metric_names[0]
        body = json.dumps({first: 4, f"{first}_reasoning": "r"})
        judge = FakeJudge(f"```json\n{body}\n```")

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
        """Wiring: with no expected_output, case themes come from `case.inputs` themes."""
        judge = FakeJudge("{}")

        await self._evaluate(
            judge,
            inputs={"themes": _themes("INPUT_ONLY")},
            output={"themes": _themes("OUTPUT_ONLY")},
        )

        prompt = judge.prompts[0]
        assert prompt.index("INPUT_ONLY") < prompt.index("OUTPUT_ONLY")


class TestRefinementQualityEvaluator(_NumericKeyJudgeTests):
    """RefinementQualityEvaluator — the numeric-key path over its two
    quality metrics. Same inherited `_build_scores` as condensation, so it
    inherits the full numeric-key contract and only pins its own `metric_names`."""

    evaluator_cls = RefinementQualityEvaluator
    metric_names = evaluator_cls.metric_names

    async def test_reads_themes_from_common_output_schema(self):
        judge = FakeJudge("{}")

        await self._evaluate(
            judge,
            inputs={"themes": _themes("INPUT_ONLY")},
            output={"themes": _themes("OUTPUT_ONLY")},
        )

        prompt = judge.prompts[0]
        assert prompt.index("INPUT_ONLY") < prompt.index("OUTPUT_ONLY")

    async def test_prompt_no_longer_evaluates_fluency(self):
        judge = FakeJudge("{}")

        await self._evaluate(judge)

        assert "fluency" not in judge.prompts[0].lower()


class TestClarityEvaluator(_JudgeContractTests):
    """ClarityEvaluator — one binary judgement per refined theme."""

    evaluator_cls = ClarityEvaluator

    async def test_scores_pass_and_fail_themes_with_failure_reasoning(self):
        judge = SequenceFakeJudge(
            '{"decision": "PASS", "reasoning": "Simple and direct."}',
            '{"decision": "FAIL", "reasoning": "Uses unexplained jargon."}',
        )
        output = {"themes": _themes("Clear theme", "Unclear theme")}

        scores = await self._evaluate(judge, output=output)

        assert scores == [
            Score(
                "clarity",
                0.5,
                "1/2 themes passed\n"
                "Failed:\n"
                "  Unclear theme — Uses unexplained jargon.",
            )
        ]
        assert len(judge.prompts) == 2

    async def test_prompts_contain_only_the_theme_being_judged(self):
        judge = FakeJudge('{"decision": "PASS", "reasoning": "Clear."}')
        output = {
            "themes": [
                {
                    "topic_label": "TARGET_ALPHA",
                    "topic_description": "TARGET_DESCRIPTION",
                },
                {
                    "topic_label": "PEER_OMEGA",
                    "topic_description": "PEER_DESCRIPTION",
                },
            ]
        }

        await self._evaluate(
            judge,
            inputs={"themes": _themes("ORIGINAL_ONLY")},
            output=output,
        )

        assert len(judge.prompts) == 2
        assert all(
            marker in judge.prompts[0]
            for marker in ("TARGET_ALPHA", "TARGET_DESCRIPTION")
        )
        assert all(
            marker not in judge.prompts[0]
            for marker in ("PEER_OMEGA", "PEER_DESCRIPTION", "ORIGINAL_ONLY")
        )
        assert all(
            marker in judge.prompts[1] for marker in ("PEER_OMEGA", "PEER_DESCRIPTION")
        )
        assert all(
            marker not in judge.prompts[1]
            for marker in ("TARGET_ALPHA", "TARGET_DESCRIPTION", "ORIGINAL_ONLY")
        )

    async def test_scores_a_single_theme(self):
        judge = FakeJudge('{"decision": "PASS", "reasoning": "Clear."}')
        output = {"themes": _themes("Clear theme", description="Plain description.")}

        scores = await self._evaluate(judge, output=output)

        assert scores == [Score("clarity", 1.0, "1/1 themes passed")]
        assert len(judge.prompts) == 1

    async def test_no_themes_skips_llm_call(self):
        judge = FakeJudge()

        scores = await self._evaluate(judge, output={"themes": []})

        assert judge.prompts == []
        assert scores == [Score("clarity", 0.0, "0/0 themes passed")]

    async def test_malformed_judge_output_degrades_to_zero_score(self):
        judge = FakeJudge("not JSON")

        scores = await self._evaluate(judge)

        assert scores[0].name == "clarity"
        assert scores[0].value == 0.0
        assert scores[0].comment.startswith("Error:")


class TestTitleSpecificityEvaluator(_JudgeContractTests):
    """TitleSpecificityEvaluator — one binary judgement per output title."""

    evaluator_cls = TitleSpecificityEvaluator

    async def test_scores_pass_and_fail_titles_independently(self):
        """Each title gets its own PASS/FAIL decision and contributes to the ratio."""
        judge = SequenceFakeJudge(
            '{"decision": "PASS", "reasoning": "Concrete issue and context."}',
            '{"decision": "FAIL", "reasoning": "Too generic."}',
        )
        output = {"themes": _themes("Housing costs in cities", "Stuff")}

        scores = await self._evaluate(judge, output=output)

        assert scores[0].name == "specificity"
        assert scores[0].value == 0.5
        assert scores[0].comment == "1/2 titles passed\nFailed: Stuff"
        assert len(judge.prompts) == 2

    async def test_prompts_contain_only_the_title_being_judged(self):
        """Peer titles are not supplied as specificity context."""
        judge = FakeJudge('{"decision": "PASS", "reasoning": "Concrete."}')
        output = {"themes": _themes("TARGET_ALPHA", "PEER_OMEGA")}

        await self._evaluate(judge, output=output)

        assert len(judge.prompts) == 2
        assert "TARGET_ALPHA" in judge.prompts[0]
        assert "PEER_OMEGA" not in judge.prompts[0]
        assert "PEER_OMEGA" in judge.prompts[1]
        assert "TARGET_ALPHA" not in judge.prompts[1]

    async def test_scores_a_single_title(self):
        """A singleton output still produces one binary judgement."""
        judge = FakeJudge('{"decision": "PASS", "reasoning": "Concrete."}')
        output = {"themes": _themes("Housing costs in cities")}

        scores = await self._evaluate(judge, output=output)

        assert scores == [Score("specificity", 1.0, "1/1 titles passed")]
        assert len(judge.prompts) == 1

    async def test_no_titles_skips_llm_call(self):
        """No titles skips the LLM call and yields the empty-case specificity score."""
        judge = FakeJudge()

        scores = await self._evaluate(judge, output={"themes": []})

        assert judge.prompts == []
        assert scores == [Score("specificity", 0.0, "0/0 titles passed")]

    async def test_malformed_judge_output_degrades_to_zero_score(self):
        """Malformed JSON follows the standard evaluator error path."""
        judge = FakeJudge("not JSON")

        scores = await self._evaluate(judge)

        assert scores[0].name == "specificity"
        assert scores[0].value == 0.0
        assert scores[0].comment.startswith("Error:")


class _PassOnJudge(FakeJudge):
    """Judge that passes an item only if it is the pass_on item, in either direction"""

    def __init__(self, pass_on, **kwargs):
        self.pass_on = pass_on
        super().__init__(**kwargs)

    async def ainvoke(self, prompt: str):
        source_items = prompt.split("## Source item")[1].split("## Candidate items")[0]
        decision = "PASS" if self.pass_on in source_items else "FAIL"
        self.parsed = json.dumps({"decision": decision})
        return await super().ainvoke(prompt)


class TestGroundInformationEvaluator(_JudgeContractTests):
    """GroundednessInformationRetentionEvaluator — original themes judged against
    refined ones gives retention, the reverse gives groundedness, F1 combines them."""

    evaluator_cls = GroundednessInformationRetentionEvaluator

    async def test_dropped_theme_lowers_retention_not_groundedness(self):
        """Every refined theme has an original, but one original was lost."""
        scores = await self._evaluate(
            _PassOnJudge("Ban"),
            expected_output={"themes": _themes("Ban", "Age")},
            output={"themes": _themes("Ban")},
        )
        by_name = {score.name: score for score in scores}

        assert by_name["groundedness"].value == 1.0
        assert by_name["information_retention"].value == 0.5
        assert by_name["f1_score"].value == 0.67
        assert "Lost: Age" in by_name["information_retention"].comment

    async def test_invented_theme_lowers_groundedness_not_retention(self):
        """No original is lost, but one refined theme has no original behind it."""
        scores = await self._evaluate(
            _PassOnJudge("Ban"),
            expected_output={"themes": _themes("Ban")},
            output={"themes": _themes("Ban", "Tax")},
        )
        by_name = {score.name: score for score in scores}

        assert by_name["groundedness"].value == 0.5
        assert by_name["information_retention"].value == 1.0
        assert "Ungrounded: Tax" in by_name["groundedness"].comment

    async def test_f1_is_zero_when_nothing_matches(self):
        scores = await self._evaluate(
            _PassOnJudge("Ban"),
            expected_output={"themes": _themes("Age")},
            output={"themes": _themes("Tax")},
        )

        assert [score.value for score in scores] == [0.0, 0.0, 0.0]

    async def test_empty_refined_themes_scores_zero_without_judge_calls(self):
        judge = FakeJudge()
        case = make_case(expected_output={"themes": _themes("Ban")})

        scores = await GroundednessInformationRetentionEvaluator(judge).evaluate(
            case, {"themes": []}
        )

        assert judge.prompts == []
        assert [score.value for score in scores] == [0.0, 0.0, 0.0]
