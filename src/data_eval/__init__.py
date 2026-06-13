"""data-eval — AI evals framework for data and analytics engineering teams."""

from typing import TYPE_CHECKING, Any

from data_eval.core import assert_eval
from data_eval.loaders import eval_case
from data_eval.scorers import ExpectationSuiteScorer, ResultSetEquivalence
from data_eval.solvers import CallableSolver
from data_eval.types import EvalCase, PlatformRef

if TYPE_CHECKING:
    from data_eval.solvers import PromptSolver as PromptSolver

__all__ = [
    "CallableSolver",
    "EvalCase",
    "ExpectationSuiteScorer",
    "PlatformRef",
    "ResultSetEquivalence",
    "assert_eval",
    "eval_case",
]


def __getattr__(name: str) -> Any:
    if name == "PromptSolver":
        from data_eval.solvers import PromptSolver

        return PromptSolver
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)


def __dir__() -> list[str]:
    return sorted([*globals(), "PromptSolver"])
