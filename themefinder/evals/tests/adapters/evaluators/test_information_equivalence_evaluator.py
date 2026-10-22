"""Tests for InformationEquivalenceEvaluator."""

from adapters.evaluators.information_equivalence_evaluator import (
    InformationEquivalenceEvaluator,
)
from conftest import _themes, make_case
from eval_types import Score
from fakes import SequenceFakeJudge


class TestInformationEquivalenceEvaluator:
    async def test_empty_lists_return_the_base_error_without_judging(self):
        judge = SequenceFakeJudge()
        evaluator = InformationEquivalenceEvaluator(judge)
        case = make_case(inputs={"themes": []})

        scores = await evaluator.evaluate(case, {"themes": []})

        assert judge.prompts == []
        assert scores == [
            Score(
                "information_equivalence",
                0.0,
                "Error: Both lists are empty; nothing to judge",
            )
        ]

    async def test_scores_one_empty_list_as_zero_without_judging(self):
        judge = SequenceFakeJudge()
        evaluator = InformationEquivalenceEvaluator(judge)
        case = make_case(inputs={"themes": _themes("Original A")})

        scores = await evaluator.evaluate(case, {"themes": []})

        assert judge.prompts == []
        assert scores == [
            Score(
                "information_equivalence",
                0.0,
                "0/1 reciprocal one-to-one pairs; list length difference: 1\n"
                "Original→refined claimed pairs: none\n"
                "Refined→original claimed pairs: none\n"
                "Reciprocal pairs: none",
            )
        ]

    async def test_judges_each_list_in_both_directions_and_aggregates_matches(self):
        judge = SequenceFakeJudge(
            '{"decision": "PASS", "matched_items": ["Refined A: desc"]}',
            '{"decision": "PASS", "matched_items": ["Refined B: desc"]}',
            '{"decision": "PASS", "matched_items": ["Original A: desc"]}',
            '{"decision": "PASS", "matched_items": ["Original B: desc"]}',
        )
        evaluator = InformationEquivalenceEvaluator(judge)
        case = make_case(inputs={"themes": _themes("Original A", "Original B")})

        scores = await evaluator.evaluate(
            case,
            {"themes": _themes("Refined A", "Refined B")},
        )

        assert len(judge.prompts) == 4
        assert "same substantive theme" in judge.prompts[0]
        assert "Original A: desc" in judge.prompts[0]
        assert "Refined A: desc" in judge.prompts[0]
        assert scores == [
            Score(
                "information_equivalence",
                1.0,
                "2/2 reciprocal one-to-one pairs; list length difference: 0\n"
                "Original→refined claimed pairs: 1→1, 2→2\n"
                "Refined→original claimed pairs: 1→1, 2→2\n"
                "Reciprocal pairs: 1→1, 2→2",
            )
        ]

    async def test_scores_missing_original_theme_as_partial_equivalence(self):
        judge = SequenceFakeJudge(
            '{"decision": "PASS", "matched_items": ["Refined A: desc"]}',
            '{"decision": "FAIL", "matched_items": "None"}',
            '{"decision": "PASS", "matched_items": ["Original A: desc"]}',
        )
        evaluator = InformationEquivalenceEvaluator(judge)
        case = make_case(inputs={"themes": _themes("Original A", "Original B")})

        scores = await evaluator.evaluate(case, {"themes": _themes("Refined A")})

        assert scores == [
            Score(
                "information_equivalence",
                0.5,
                "1/2 reciprocal one-to-one pairs; list length difference: 1\n"
                "Original→refined claimed pairs: 1→1\n"
                "Refined→original claimed pairs: 1→1\n"
                "Reciprocal pairs: 1→1",
            )
        ]

    async def test_ignores_a_pass_with_an_unknown_matched_item(self):
        judge = SequenceFakeJudge(
            '{"decision": "PASS", "matched_items": ["Unknown"]}',
            '{"decision": "PASS", "matched_items": ["Original A: desc"]}',
        )
        evaluator = InformationEquivalenceEvaluator(judge)
        case = make_case(inputs={"themes": _themes("Original A")})

        scores = await evaluator.evaluate(case, {"themes": _themes("Refined A")})

        assert scores == [
            Score(
                "information_equivalence",
                0.0,
                "0/1 reciprocal one-to-one pairs; list length difference: 0\n"
                "Original→refined claimed pairs: none\n"
                "Refined→original claimed pairs: 1→1\n"
                "Reciprocal pairs: none",
            )
        ]

    async def test_discards_one_to_many_matches(self):
        judge = SequenceFakeJudge(
            '{"decision": "PASS", "matched_items": ["Refined A: desc", "Refined B: desc"]}',
            '{"decision": "PASS", "matched_items": ["Original A: desc"]}',
            '{"decision": "PASS", "matched_items": ["Original A: desc"]}',
        )
        evaluator = InformationEquivalenceEvaluator(judge)
        case = make_case(inputs={"themes": _themes("Original A")})

        scores = await evaluator.evaluate(
            case,
            {"themes": _themes("Refined A", "Refined B")},
        )

        assert scores[0].value == 0.0
        assert "Original→refined claimed pairs: none" in scores[0].comment

    async def test_requires_directional_pairings_to_agree(self):
        judge = SequenceFakeJudge(
            '{"decision": "PASS", "matched_items": ["Refined A: desc"]}',
            '{"decision": "PASS", "matched_items": ["Refined B: desc"]}',
            '{"decision": "PASS", "matched_items": ["Original B: desc"]}',
            '{"decision": "PASS", "matched_items": ["Original A: desc"]}',
        )
        evaluator = InformationEquivalenceEvaluator(judge)
        case = make_case(inputs={"themes": _themes("Original A", "Original B")})

        scores = await evaluator.evaluate(
            case,
            {"themes": _themes("Refined A", "Refined B")},
        )

        assert scores == [
            Score(
                "information_equivalence",
                0.0,
                "0/2 reciprocal one-to-one pairs; list length difference: 0\n"
                "Original→refined claimed pairs: 1→1, 2→2\n"
                "Refined→original claimed pairs: 1→2, 2→1\n"
                "Reciprocal pairs: none",
            )
        ]
