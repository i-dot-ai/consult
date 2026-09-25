"""Tests for PydanticEvalsEvaluator — the bridge that runs any native
pydantic-evals Evaluator behind this framework's EvaluatorPort.
"""

import pytest
from dataclasses import dataclass
from typing import Any, ClassVar

import pydantic_evals.evaluators.llm_as_a_judge as laj
from pydantic_evals.evaluators.common import LLMJudge, OutputConfig
from pydantic_evals.evaluators.llm_as_a_judge import GradingOutput

from adapters.evaluators.pydantic_evals import PydanticEvalsEvaluator

from conftest import make_case
from eval_types import Score
from pydantic_evals.evaluators import (
    Contains,
    Equals,
    EqualsExpected,
    Evaluator,
    EvaluatorContext,
)

# Real built-in evaluators, each run offline through the adapter.
REAL_EVALUATOR_CASES = [
    pytest.param(
        Equals(value=5), 5, None, [Score("Equals", 1.0, "")], id="equals-match"
    ),
    pytest.param(
        Equals(value=5), 4, None, [Score("Equals", 0.0, "")], id="equals-miss"
    ),
    pytest.param(
        EqualsExpected(), 5, 5, [Score("EqualsExpected", 1.0, "")], id="expected-match"
    ),
    pytest.param(
        EqualsExpected(), 4, 5, [Score("EqualsExpected", 0.0, "")], id="expected-miss"
    ),
    pytest.param(
        Contains(value="zzz"),
        "abc",
        None,
        [
            Score(
                "Contains",
                0.0,
                "Output string 'abc' does not contain expected string 'zzz'",
            )
        ],
        id="contains-miss-with-reason",
    ),
]


# --- local fakes, only for adapter-specific projection behaviour no built-in exercises


@dataclass
class LabelEval(Evaluator):
    """Returns a bare str, which pydantic-evals treats as a label — no numeric value."""

    label: ClassVar[str] = "categorised"

    def evaluate(self, ctx: EvaluatorContext) -> str:
        return self.label


@dataclass
class MultiMetricEval(Evaluator):
    """Returns a multi-key mapping, one Score per key."""

    scores: ClassVar[dict[str, float]] = {"precision": 0.8, "recall": 0.6}

    def evaluate(self, ctx: EvaluatorContext) -> dict[str, Any]:
        return dict(self.scores)


@dataclass
class RaisingEval(Evaluator):
    """Raises when run, to exercise EvaluatorPort.evaluate()'s error boundary."""

    def evaluate(self, ctx: EvaluatorContext) -> float:
        raise RuntimeError("boom")


class TestPydanticEvalsEvaluator:
    @pytest.mark.parametrize(
        "evaluator, output, expected_output, expected_scores", REAL_EVALUATOR_CASES
    )
    async def test_real_evaluators_produce_sensible_scores(
        self, evaluator, output, expected_output, expected_scores
    ):
        """Every wrapped real evaluator returns the expected list[Score]."""
        scores = await PydanticEvalsEvaluator(evaluator).evaluate(
            make_case(expected_output=expected_output), output
        )

        assert scores == expected_scores

    async def test_failure_degrades_to_zero_scores_over_declared_metric_names(self):
        """A raising evaluator degrades to one zero Score per declared metric name."""
        adapter = PydanticEvalsEvaluator(RaisingEval())

        assert adapter.metric_names == ("RaisingEval",)
        scores = await adapter.evaluate(make_case(), "abc")

        assert [s.name for s in scores] == ["RaisingEval"]
        assert all(s.value == 0.0 for s in scores)
        assert all(s.comment.startswith("Error:") for s in scores)

    async def test_wraps_real_llm_judge(self, monkeypatch):
        """Test we can wrap a pydantic-eval llm judge, stubbed here."""

        async def fake_judge_output(output, rubric, model, model_settings):
            return GradingOutput(reason="looks grounded", pass_=True, score=0.8)

        monkeypatch.setattr(laj, "judge_output", fake_judge_output)

        judge = LLMJudge(
            rubric="are the themes grounded?",
            score=OutputConfig(),
            assertion=OutputConfig(include_reason=True),
        )
        adapter = PydanticEvalsEvaluator(
            judge, metric_names=("LLMJudge_score", "LLMJudge_pass")
        )

        assert adapter.metric_names == ("LLMJudge_score", "LLMJudge_pass")
        scores = await adapter.evaluate(make_case(), {"themes": {}})

        assert scores == [
            Score("LLMJudge_score", 0.8, ""),
            Score("LLMJudge_pass", 1.0, "looks grounded"),
        ]

    def test_pydantic_evaluator_exposes_wrapped_evaluator_for_a_native_runner(self):
        """`pydantic_evaluator` hands back the wrapped native Evaluator for a native runner."""
        evaluator = Equals(value=5)
        adapter = PydanticEvalsEvaluator(evaluator)

        assert adapter.pydantic_evaluator is evaluator

    async def test_str_label_recorded_in_comment_with_zero_value(self):
        """A bare str label parks in the comment at value 0.0 rather than coercing."""
        scores = await PydanticEvalsEvaluator(LabelEval()).evaluate(make_case(), {})

        assert scores == [Score("LabelEval", 0.0, LabelEval.label)]

    async def test_multi_key_mapping_projects_onto_declared_names(self):
        """A multi-output evaluator projects each declared name onto its mapping key."""
        expected = MultiMetricEval.scores
        adapter = PydanticEvalsEvaluator(
            MultiMetricEval(), metric_names=tuple(expected)
        )

        scores = await adapter.evaluate(make_case(), {})

        assert scores == [Score(name, value, "") for name, value in expected.items()]

    async def test_declared_names_mismatch_degrades_gracefully(self):
        """Declaring names that don't match the evaluator's emitted keys results in fail"""
        adapter = PydanticEvalsEvaluator(MultiMetricEval(), metric_names=("f1",))

        scores = await adapter.evaluate(make_case(), {})

        assert [s.name for s in scores] == ["f1"]
        assert all(s.value == 0.0 for s in scores)
        assert all(s.comment.startswith("Error:") for s in scores)
