"""EvaluatorPort — the port every evaluator adapter implements.

Deliberately narrow: one method, scoring a single case's task output.
`EvalRunnerPort` implementations invoke this once per case, per evaluator,
and stay agnostic to which kind of evaluator (LLM judge, deterministic
metric, embedding-based) they're driving.

Dataset-level aggregation (mean/std per metric across a run) deliberately
lives elsewhere, not on this port — see the "Deliberately out of scope"
section of the PRO-729 plan. An evaluator only ever sees one case per call;
aggregating here would mean accumulating state across concurrent `evaluate()`
calls, which a stateless per-case scorer avoids entirely. That's a
RunReport/EvalRunnerPort-level concern instead.
"""

from abc import ABC, abstractmethod
from typing import Any

from eval_types import Case, Score


class EvaluatorPort(ABC):
    @abstractmethod
    async def evaluate(self, case: Case, output: Any) -> list[Score]:
        """Score `output` (the task's result for `case`) and return one or more Scores.

        Always declared `async def`, even for evaluators whose body never
        awaits anything (deterministic or embedding-based evaluators) —
        callers always `await evaluate(...)` uniformly.
        """
