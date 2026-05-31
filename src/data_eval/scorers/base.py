"""`Scorer` Protocol: pluggable pass/fail check over an executed result."""

from typing import Protocol, runtime_checkable

from data_eval.types import EvalCase, ExecutionResult, ScoreResult, SolverOutput


@runtime_checkable
class Scorer(Protocol):
    """Produces a `ScoreResult` from a case, its solver output, and the execution result."""

    def score(self, case: EvalCase, output: SolverOutput, result: ExecutionResult) -> ScoreResult:
        """Decide pass/fail with diagnostics for `case` given `output` and `result`."""
        ...
