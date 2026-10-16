"""Tests for InformationEquivalenceEvaluator."""

from types import SimpleNamespace

from adapters.evaluators.information_equivalence_evaluator import (
    InformationEquivalenceEvaluator,
)
from conftest import _themes, make_case
from eval_types import Score


class _SequenceJudge:
    def __init__(self, *responses: str):
        self.responses = iter(responses)
        self.prompts: list[str] = []

    async def ainvoke(self, prompt: str) -> SimpleNamespace:
        self.prompts.append(prompt)
        return SimpleNamespace(parsed=next(self.responses))


class TestInformationEquivalenceEvaluator:
    async def test_judges_each_list_in_both_directions_and_aggregates_matches(self):
        judge = _SequenceJudge(
            '{"decision": "YES", "matched_candidate_id": 1}',
            '{"decision": "YES", "matched_candidate_id": 2}',
            '{"decision": "YES", "matched_candidate_id": 1}',
            '{"decision": "YES", "matched_candidate_id": 2}',
        )
        evaluator = InformationEquivalenceEvaluator(judge)
        case = make_case(inputs={"themes": _themes("Original A", "Original B")})

        scores = await evaluator.evaluate(
            case,
            {"themes": _themes("Refined A", "Refined B")},
        )

        assert len(judge.prompts) == 4
        assert "exactly one candidate theme" in judge.prompts[0]
        assert '"id": 1' in judge.prompts[0]
        assert "Refined A: desc" in judge.prompts[0]
        assert "Original A: desc" in judge.prompts[0]
        assert scores == [
            Score(
                "information_equivalence",
                1.0,
                "2/2 reciprocal one-to-one pairs; list length difference: 0\n"
                "Refined→original claimed pairs: 1→1, 2→2\n"
                "Original→refined claimed pairs: 1→1, 2→2\n"
                "Reciprocal pairs: 1→1, 2→2",
            )
        ]

    async def test_scores_missing_original_theme_as_partial_equivalence(self):
        judge = _SequenceJudge(
            '{"decision": "YES", "matched_candidate_id": 1}',
            '{"decision": "YES", "matched_candidate_id": 1}',
            '{"decision": "NO"}',
        )
        evaluator = InformationEquivalenceEvaluator(judge)
        case = make_case(inputs={"themes": _themes("Original A", "Original B")})

        scores = await evaluator.evaluate(case, {"themes": _themes("Refined A")})

        assert scores == [
            Score(
                "information_equivalence",
                0.5,
                "1/2 reciprocal one-to-one pairs; list length difference: 1\n"
                "Refined→original claimed pairs: 1→1\n"
                "Original→refined claimed pairs: 1→1\n"
                "Reciprocal pairs: 1→1",
            )
        ]

    async def test_ignores_a_yes_decision_with_an_invalid_candidate_id(self):
        judge = _SequenceJudge(
            '{"decision": "YES", "matched_candidate_id": 2}',
            '{"decision": "YES", "matched_candidate_id": 1}',
        )
        evaluator = InformationEquivalenceEvaluator(judge)
        case = make_case(inputs={"themes": _themes("Original A")})

        scores = await evaluator.evaluate(case, {"themes": _themes("Refined A")})

        assert scores == [
            Score(
                "information_equivalence",
                0.0,
                "0/1 reciprocal one-to-one pairs; list length difference: 0\n"
                "Refined→original claimed pairs: none\n"
                "Original→refined claimed pairs: 1→1\n"
                "Reciprocal pairs: none",
            )
        ]

    async def test_requires_directional_pairings_to_agree(self):
        judge = _SequenceJudge(
            '{"decision": "YES", "matched_candidate_id": 1}',
            '{"decision": "YES", "matched_candidate_id": 2}',
            '{"decision": "YES", "matched_candidate_id": 2}',
            '{"decision": "YES", "matched_candidate_id": 1}',
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
                "Refined→original claimed pairs: 1→1, 2→2\n"
                "Original→refined claimed pairs: 1→2, 2→1\n"
                "Reciprocal pairs: none",
            )
        ]
