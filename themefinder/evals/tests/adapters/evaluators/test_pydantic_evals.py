"""Tests for PydanticEvalsEvaluator — the bridge that runs any native
pydantic-evals Evaluator behind this framework's EvaluatorPort.

These drive the *real* built-in pydantic-evals evaluators wherever possible
(`Equals`, `EqualsExpected`, `Contains`, `IsInstance`, `LLMJudge`), so the adapter
is exercised against the library's genuine context-reading, output shapes and
naming conventions — not just fakes written to its contract. None make a network
call; the one `LLMJudge` test stubs the underlying judge coroutine so it stays
offline too.

Three small local `Evaluator` fakes remain at the bottom, for adapter-specific
behaviour no built-in exercises cleanly: a `str` label, an unpredictable multi-key
mapping, and one that raises to hit the error boundary.

`metric_names` is derived from the wrapped evaluator, not passed in, so tests
assert on the derived names as well as the values.
"""

from dataclasses import dataclass
from typing import Any

import pytest
from adapters.evaluators.base import EvaluatorPort
from adapters.evaluators.pydantic_evals import (
    PydanticEvalsEvaluator,
    gateway_judge_model,
)
from conftest import make_case, set_gateway_credentials
from eval_types import Score
from pydantic_evals.evaluators import (
    Contains,
    Equals,
    EqualsExpected,
    Evaluator,
    EvaluatorContext,
    IsInstance,
)

# Real built-in evaluators, each run offline through the adapter. Every row covers a
# different EvaluatorOutput shape: a bare bool (Equals/EqualsExpected), an
# EvaluationReason with no reason (success) and with a reason (failure). Together they
# exercise context wiring (EqualsExpected reads expected_output; the rest read output),
# scalar→float mapping, reason→comment mapping and name derivation. Each row is
# (evaluator, output, expected_output, expected_scores).
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
        Contains(value="hi"),
        "say hi there",
        None,
        [Score("Contains", 1.0, "")],
        id="contains-hit",
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
    pytest.param(
        IsInstance(type_name="dict"),
        {"a": 1},
        None,
        [Score("IsInstance", 1.0, "")],
        id="isinstance-ok",
    ),
    pytest.param(
        IsInstance(type_name="dict"),
        "s",
        None,
        [Score("IsInstance", 0.0, "output is of type str")],
        id="isinstance-wrong-with-reason",
    ),
]


# --- local fakes, only for adapter-specific projection behaviour no built-in exercises


@dataclass
class LabelEval(Evaluator):
    """Returns a bare str, which pydantic-evals treats as a label — no numeric value."""

    def evaluate(self, ctx: EvaluatorContext) -> str:
        return "categorised"


@dataclass
class UnpredictableMappingEval(Evaluator):
    """Returns a multi-key mapping whose keys the adapter can't predict from config."""

    def evaluate(self, ctx: EvaluatorContext) -> dict[str, Any]:
        return {"precision": 0.8, "recall": 0.6}


@dataclass
class RaisingEval(Evaluator):
    """Raises when run, to exercise EvaluatorPort.evaluate()'s error boundary."""

    def evaluate(self, ctx: EvaluatorContext) -> float:
        raise RuntimeError("boom")


class TestPydanticEvalsEvaluator:
    def test_is_evaluator_port(self):
        assert isinstance(PydanticEvalsEvaluator(Equals(value=5)), EvaluatorPort)

    @pytest.mark.parametrize(
        "evaluator, output, expected_output, expected_scores", REAL_EVALUATOR_CASES
    )
    async def test_real_evaluators_produce_sensible_scores(
        self, evaluator, output, expected_output, expected_scores
    ):
        """Every wrapped real evaluator returns a well-formed list[Score] — each a
        Score with a str name, a float value and a str comment — matching the
        expected values."""
        scores = await PydanticEvalsEvaluator(evaluator).evaluate(
            make_case(expected_output=expected_output), output
        )

        assert isinstance(scores, list)
        assert all(isinstance(s, Score) for s in scores)
        assert all(isinstance(s.name, str) for s in scores)
        assert all(isinstance(s.value, float) for s in scores)
        assert all(isinstance(s.comment, str) for s in scores)
        assert scores == expected_scores

    async def test_failure_degrades_to_zero_scores_over_derived_metric_names(self):
        """When the wrapped evaluator raises, EvaluatorPort.evaluate()'s error boundary
        turns it into one zero Score per derived metric name — the same name a
        successful run would emit — rather than propagating. This keeps score names
        stable across cases, including cases where the wrapped evaluator errors, which
        is what cross-case aggregation relies on."""
        adapter = PydanticEvalsEvaluator(RaisingEval())

        assert adapter.metric_names == ("RaisingEval",)
        scores = await adapter.evaluate(make_case(), "abc")

        assert [s.name for s in scores] == ["RaisingEval"]
        assert all(s.value == 0.0 for s in scores)
        assert all(s.comment.startswith("Error:") for s in scores)

    async def test_wraps_real_llm_judge(self, monkeypatch):
        """Headline use case (ADR-0011 'use pydantic-evals for LAJ'): wrap the native
        LLMJudge. The underlying judge coroutine is stubbed so no model is called, and
        LLMJudge.evaluate is async — so this also covers the async evaluate_async path.

        A judge with both `score` and `assertion` set emits keys `LLMJudge_score` and
        `LLMJudge_pass`; the adapter derives exactly those names, so the projection
        matches every key the judge returns."""
        import pydantic_evals.evaluators.llm_as_a_judge as laj
        from pydantic_evals.evaluators.common import LLMJudge, OutputConfig
        from pydantic_evals.evaluators.llm_as_a_judge import GradingOutput

        async def fake_judge_output(output, rubric, model, model_settings):
            return GradingOutput(reason="looks grounded", pass_=True, score=0.8)

        monkeypatch.setattr(laj, "judge_output", fake_judge_output)

        judge = LLMJudge(
            rubric="are the themes grounded?",
            score=OutputConfig(),
            assertion=OutputConfig(include_reason=True),
        )
        adapter = PydanticEvalsEvaluator(judge)

        assert adapter.metric_names == ("LLMJudge_score", "LLMJudge_pass")
        scores = await adapter.evaluate(make_case(), {"themes": {}})

        assert scores == [
            Score("LLMJudge_score", 0.8, ""),
            Score("LLMJudge_pass", 1.0, "looks grounded"),
        ]

    def test_gateway_judge_model_points_at_the_gateway(self, monkeypatch):
        """gateway_judge_model builds a pydantic-ai OpenAIChatModel for a gateway
        model-group name, pointed at the gateway's OpenAI-compatible endpoint via the
        shared credentials — the model a wrapped LLMJudge would call. No request made."""
        set_gateway_credentials(
            monkeypatch, url="https://gateway.example.invalid", api_key="k"
        )

        model = gateway_judge_model("claude-sonnet-4")

        assert model.model_name == "claude-sonnet-4"
        assert str(model.client.base_url).startswith("https://gateway.example.invalid")

    async def test_str_label_recorded_in_comment_with_zero_value(self):
        scores = await PydanticEvalsEvaluator(LabelEval()).evaluate(make_case(), {})

        assert scores == [Score("LabelEval", 0.0, "categorised")]

    async def test_unpredictable_mapping_keys_are_dropped(self):
        """An evaluator returning a multi-key mapping we can't predict has only its
        default name derived; that name isn't a key it returned, so it degrades to a
        zero Score and the real keys are dropped."""
        adapter = PydanticEvalsEvaluator(UnpredictableMappingEval())

        assert adapter.metric_names == ("UnpredictableMappingEval",)
        scores = await adapter.evaluate(make_case(), {})

        assert scores == [
            Score("UnpredictableMappingEval", 0.0, "Not returned by evaluator")
        ]
