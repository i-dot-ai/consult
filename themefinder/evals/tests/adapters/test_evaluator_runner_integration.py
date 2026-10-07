"""Integration tests: check each RunnerPort adapter can actually run the EvaluatorPort adapters"""

from dataclasses import dataclass
from typing import Any

import pydantic_evals.evaluators.llm_as_a_judge as llm_as_a_judge_module
from pydantic_evals.evaluators import Evaluator, EvaluatorContext
from pydantic_evals.evaluators.common import EqualsExpected, LLMJudge, OutputConfig
from pydantic_evals.evaluators.llm_as_a_judge import GradingOutput

from adapters.evaluators.groundedness_evaluator import GroundednessEvaluator
from adapters.evaluators.mapping_f1_evaluator import MappingF1Evaluator
from adapters.evaluators.pydantic_evals_evaluator import PydanticEvalsEvaluator
from adapters.runners.base import RunnerPort
from adapters.runners.inline_sequential_runner import InlineSequentialRunner
from adapters.runners.pydantic_evals_runner import PydanticEvalsRunner
from conftest import make_case
from eval_types import Case, ComponentConfig
from fakes import FakeJudge


class _EvaluatorRunnerIntegrationTests:
    """One shared case/task/evaluator-set; subclasses provide make_runner()."""

    def make_runner(self) -> RunnerPort:
        raise NotImplementedError

    @staticmethod
    async def _task(inputs: dict, llm: Any) -> dict:
        return {"themes": inputs["themes"], "labels": {"r1": ["A"], "r2": ["B"]}}

    @staticmethod
    def _cases() -> list[Case]:
        # MappingF1Evaluator's sklearn f1_score(average="samples") needs at
        # least two distinct labels to be treated as multilabel-indicator,
        # hence two responses/labels here rather than one.
        themes = [{"topic_label": "A", "topic_description": "desc a"}]
        return [
            make_case(
                inputs={"themes": themes},
                expected_output={
                    "themes": themes,
                    "mappings": {"r1": ["A"], "r2": ["B"]},
                },
                case_id="case-1",
            )
        ]

    @staticmethod
    def _evaluators(monkeypatch) -> list:
        async def fake_judge_output(output, rubric, model, model_settings):
            return GradingOutput(reason="looks good", pass_=True, score=0.9)

        monkeypatch.setattr(llm_as_a_judge_module, "judge_output", fake_judge_output)

        groundedness_judge = FakeJudge(
            '{"evaluations": {"A": {"decision": "STRONG", "matched_to": "A", "reasoning": "matches"}}}'
        )
        llm_judge = LLMJudge(
            rubric="are the themes grounded?",
            score=OutputConfig(),
            assertion=OutputConfig(include_reason=True),
        )

        return [
            MappingF1Evaluator(),
            GroundednessEvaluator(groundedness_judge),
            PydanticEvalsEvaluator(EqualsExpected()),
            PydanticEvalsEvaluator(
                llm_judge, metric_names=("LLMJudge_score", "LLMJudge_pass")
            ),
        ]

    async def test_runner_runs_every_kind_of_evaluator(self, monkeypatch):
        config = ComponentConfig(
            component="mapping",
            task=self._task,
            evaluators=self._evaluators(monkeypatch),
        )

        report = await self.make_runner().run(config, self._cases(), llm="llm")

        outcome = report.outcomes[0]
        assert outcome.error is None
        scores = {score.name: score for score in outcome.scores}

        # Deterministic (MappingF1Evaluator): labels exactly match mappings.
        assert scores["f1_score"].value == 1.0
        # Our own LLM-judge evaluator (GroundednessEvaluator): fake judge said STRONG.
        assert scores["groundedness"].value == 5.0
        # Native pydantic_evals evaluator wrapped, non-LLM (EqualsExpected):
        # output != expected_output (different keys), so this deterministically fails.
        assert scores["EqualsExpected"].value == 0.0
        # Native pydantic_evals evaluator wrapped, LLM-based (LLMJudge, stubbed).
        assert scores["LLMJudge_score"].value == 0.9
        assert scores["LLMJudge_pass"].value == 1.0
        assert scores["LLMJudge_pass"].comment == "looks good"

    async def test_wrapped_native_evaluator_failure_degrades_to_zero_score(self):
        """A raising native evaluator becomes a zero score with an error comment under every runner."""

        @dataclass
        class _Raising(Evaluator):
            def evaluate(self, ctx: EvaluatorContext) -> float:
                raise RuntimeError("boom")

        config = ComponentConfig(
            component="mapping",
            task=self._task,
            evaluators=[PydanticEvalsEvaluator(_Raising())],
        )

        report = await self.make_runner().run(config, self._cases(), llm="llm")

        outcome = report.outcomes[0]
        assert outcome.error is None, (
            "evaluator failure should not fail the case itself"
        )
        assert [(s.name, s.value) for s in outcome.scores] == [("_Raising", 0.0)], (
            "failing evaluator should yield one zero score"
        )
        assert outcome.scores[0].comment.startswith("Error:"), (
            "failure should be reported in the score comment"
        )


class TestInlineSequentialRunnerIntegration(_EvaluatorRunnerIntegrationTests):
    def make_runner(self) -> RunnerPort:
        return InlineSequentialRunner()


class TestPydanticEvalsRunnerIntegration(_EvaluatorRunnerIntegrationTests):
    """Uses the real pydantic_evals.Dataset.evaluate() engine, progress=False."""

    def make_runner(self) -> RunnerPort:
        return PydanticEvalsRunner(progress=False)
