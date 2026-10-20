"""Tests for the per-item loop in BinaryMatchJudgeEvaluator via a stub child.

TODO PRO-891 Temporary: delete once a concrete child exists and its tests cover the base.
"""

import asyncio
from types import SimpleNamespace
from typing import Any

import pytest
from adapters.evaluators.llm_judge_evaluator import (
    BinaryMatchDecisions,
    BinaryMatchJudgeEvaluator,
)
from conftest import make_case
from eval_types import Case, Score
from fakes import FakeJudge


class _StubBinaryJudge(BinaryMatchJudgeEvaluator):
    """Smallest concrete child: output titles judged against expected titles,
    greppable prompt, and `_build_scores` records what the loop handed it."""

    metric_names = ("match_rate",)

    def _get_lists(self, case: Case, output: Any) -> tuple[list[str], list[str]]:
        return list(output["themes"]), list(case.expected_output["themes"])

    def _build_item_prompt(self, single_item: str, item_list: list[str]) -> str:
        return f"{single_item} || {','.join(item_list)}"

    def _build_scores(self, decisions: BinaryMatchDecisions) -> list[Score]:
        self.seen = decisions
        forward = decisions.forward
        n_pass = sum(d.get("decision") == "PASS" for d in forward)
        ratio = n_pass / len(forward) if forward else 0.0
        return [Score("match_rate", ratio, "")]


class _InFlightJudge(FakeJudge):
    """Judge that records the peak number of concurrent `ainvoke` calls."""

    def __init__(self):
        super().__init__('{"decision": "PASS"}')
        self.in_flight = 0
        self.peak = 0

    async def ainvoke(self, prompt: str) -> SimpleNamespace:
        self.in_flight += 1
        self.peak = max(self.peak, self.in_flight)
        await asyncio.sleep(0.01)  # hold the call open so concurrent calls overlap
        self.in_flight -= 1
        return await super().ainvoke(prompt)


class _RaisingJudge:
    async def ainvoke(self, prompt: str):
        raise RuntimeError("boom")


class _FailOnBJudge(FakeJudge):
    """Judge that raises for item "B" and answers every other item."""

    async def ainvoke(self, prompt: str) -> SimpleNamespace:
        await asyncio.sleep(0.01)
        if prompt.startswith("B"):
            raise RuntimeError("boom")
        return await super().ainvoke(prompt)


class TestBinaryMatchJudgeEvaluator:
    """The per-item loop, exercised through the stub child."""

    async def _run(self, judge, items, candidates, **kwargs):
        """Run the stub on `items` vs `candidates`, returning (evaluator, scores)."""
        evaluator = _StubBinaryJudge(judge, **kwargs)
        case = make_case(expected_output={"themes": candidates})
        scores = await evaluator.evaluate(case, {"themes": items})
        return evaluator, scores

    async def test_one_call_per_item_in_each_direction_in_order(self):
        """Each item gets one prompt holding it plus every candidate, then each
        candidate gets one holding it plus every item; decisions reach
        `_build_scores` in input order, tagged with the item they judged."""
        judge = FakeJudge('{"decision": "PASS"}')

        evaluator, scores = await self._run(judge, ["A", "B", "C"], ["X", "Y"])

        assert judge.prompts == [
            "A || X,Y",
            "B || X,Y",
            "C || X,Y",
            "X || A,B,C",
            "Y || A,B,C",
        ]
        assert evaluator.seen.items == ["A", "B", "C"]
        assert evaluator.seen.candidates == ["X", "Y"]
        assert [d["item"] for d in evaluator.seen.forward] == ["A", "B", "C"]
        assert [d["item"] for d in evaluator.seen.backward] == ["X", "Y"]
        assert scores == [Score("match_rate", 1.0, "")]

    async def test_judged_item_overrides_judge_supplied_item(self):
        """The base class sets `item` from what it sent, so a judge that echoes
        a wrong or paraphrased item cannot misattribute its decision."""
        judge = FakeJudge('{"item": "WRONG", "decision": "PASS"}')

        evaluator, _ = await self._run(judge, ["A", "B"], ["X"])

        assert [d["item"] for d in evaluator.seen.forward] == ["A", "B"]

    @pytest.mark.parametrize(
        ("items", "candidates"),
        [([], ["X"]), (["A", "B"], [])],
        ids=["no-items", "no-candidates"],
    )
    async def test_one_empty_list_is_decided_without_calling_llm(
        self, items, candidates
    ):
        """One empty list is a valid case answered without the judge: the
        direction with no items has no decisions, the direction with no
        candidates fails every item."""
        judge = FakeJudge('{"decision": "PASS"}')

        evaluator, scores = await self._run(judge, items, candidates)

        assert judge.prompts == []
        assert [d["item"] for d in evaluator.seen.forward] == items
        assert [d["item"] for d in evaluator.seen.backward] == candidates
        decisions = evaluator.seen.forward + evaluator.seen.backward
        assert all(d["decision"] == "FAIL" for d in decisions)
        assert scores == [Score("match_rate", 0.0, "")]

    async def test_both_lists_empty_errors_without_calling_llm(self):
        """Both empty leaves nothing to judge: no judge calls, and the case
        degrades to a zero Score carrying the error, via EvaluatorPort."""
        judge = FakeJudge()

        evaluator, scores = await self._run(judge, [], [])

        assert judge.prompts == []
        assert not hasattr(evaluator, "seen")
        assert scores == [
            Score("match_rate", 0.0, "Error: Both lists are empty; nothing to judge")
        ]

    @pytest.mark.parametrize(("concurrency", "expected_peak"), [(2, 2), (5, 5)])
    async def test_concurrency_cap(self, concurrency, expected_peak):
        """The shared semaphore caps in-flight judge calls at `concurrency`; the
        uncapped case proves the test can see real parallelism."""
        judge = _InFlightJudge()

        await self._run(judge, list("ABCDE"), ["X"], concurrency=concurrency)

        assert judge.peak == expected_peak

    async def test_judge_failure_degrades_to_zero_scores(self):
        """A failing judge degrades to one zero Score per metric, via EvaluatorPort."""
        _, scores = await self._run(_RaisingJudge(), ["A"], ["X"])

        assert scores == [Score("match_rate", 0.0, "Error: boom")]

    async def test_failure_cancels_remaining_calls(self):
        """One failing item errors the case and stops the rest of the loop,
        rather than leaving queued calls running with discarded results."""
        judge = _FailOnBJudge('{"decision": "PASS"}')

        # concurrency=1 queues C-F behind B, so they are still pending when B fails
        _, scores = await self._run(judge, list("ABCDEF"), ["X"], concurrency=1)
        calls_at_return = len(judge.prompts)
        await asyncio.sleep(0.1)  # long enough for orphaned calls to show up

        assert scores == [Score("match_rate", 0.0, "Error: boom")]
        assert len(judge.prompts) == calls_at_return
        assert calls_at_return < 6
