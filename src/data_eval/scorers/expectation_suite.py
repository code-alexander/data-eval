"""`ExpectationSuiteScorer`: evaluates an `ExpectationSuite` against an executed result."""

from collections import Counter
from typing import Any, assert_never

from data_eval.types import (
    ColumnPresenceExpectation,
    ColumnTypeExpectation,
    EvalCase,
    ExecutionResult,
    Expectation,
    ExpectationSuite,
    NotNullExpectation,
    RowCountExpectation,
    ScoreResult,
    SolverOutput,
    UniqueExpectation,
)

SCORER_NAME = "expectation_suite"


class ExpectationSuiteScorer:
    """Scores a case by checking its executed result against each `Expectation` in its suite."""

    def score(self, case: EvalCase, output: SolverOutput, result: ExecutionResult) -> ScoreResult:
        """Evaluate every expectation in the suite; pass iff all hold.

        Args:
            case: The eval case, carrying the `ExpectationSuite`.
            output: The solver output (part of the `Scorer` protocol; unused here).
            result: The executed result to check the expectations against.

        Returns:
            A `ScoreResult` that passes when all expectations hold; on failure its
            `explanation` lists each unmet expectation. A failed query yields a failing
            result with an explanation.

        Raises:
            TypeError: If `case.expected` is not an `ExpectationSuite`.
        """
        expected = case.expected
        if not isinstance(expected, ExpectationSuite):
            msg = f"ExpectationSuiteScorer requires an ExpectationSuite; got {type(expected).__name__}"
            raise TypeError(msg)

        if result.error is not None:
            return ScoreResult(
                scorer=SCORER_NAME,
                passed=False,
                explanation=f"query execution failed: {result.error}",
            )

        failures = [msg for e in expected.expectations if (msg := _evaluate_one(e, result)) is not None]
        if not failures:
            return ScoreResult(scorer=SCORER_NAME, passed=True)
        explanation = "\n".join([f"{len(failures)} expectation(s) failed:", *(f"  - {m}" for m in failures)])
        return ScoreResult(scorer=SCORER_NAME, passed=False, explanation=explanation)


def _evaluate_one(expectation: Expectation, result: ExecutionResult) -> str | None:
    """Check one expectation against `result`.

    Args:
        expectation: The expectation to check.
        result: The executed result.

    Returns:
        A human-readable failure message, or `None` if the expectation holds.
    """
    match expectation:
        case RowCountExpectation():
            actual = len(result.rows)
            if actual != expectation.exact:
                return f"row_count: expected {expectation.exact} rows, got {actual}"
            return None
        case ColumnPresenceExpectation():
            present = _result_column_names(result)
            missing = [c for c in expectation.columns if c not in present]
            if missing:
                return f"column_presence: missing column(s) {missing}"
            return None
        case ColumnTypeExpectation():
            if result.schema_ is None:
                return f"column_type: no column schema available for column {expectation.column!r}"
            types = dict(zip(result.schema_.names, result.schema_.types, strict=True))
            if expectation.column not in types:
                return f"column_type: column {expectation.column!r} not found in result"
            actual_type = types[expectation.column]
            if actual_type != expectation.expected_type:
                return (
                    f"column_type: column {expectation.column!r} expected type "
                    f"{expectation.expected_type.raw!r}, got {actual_type.raw!r}"
                )
            return None
        case NotNullExpectation():
            if expectation.column not in _result_column_names(result):
                return f"not_null: column {expectation.column!r} not found in result"
            null_count = sum(1 for row in result.rows if row.get(expectation.column) is None)
            if null_count:
                return f"not_null: column {expectation.column!r} has {null_count} NULL value(s)"
            return None
        case UniqueExpectation():
            if expectation.column not in _result_column_names(result):
                return f"unique: column {expectation.column!r} not found in result"
            counts = Counter(_hashable_key(row.get(expectation.column)) for row in result.rows)
            duplicates = [key for key, n in counts.items() if n > 1]
            if duplicates:
                sample = ", ".join(_render_key(key) for key in duplicates[:3])
                return f"unique: column {expectation.column!r} has {len(duplicates)} duplicated value(s): {sample}"
            return None
        case _:  # pragma: no cover - exhaustive over the Expectation union
            assert_never(expectation)


def _result_column_names(result: ExecutionResult) -> list[str]:
    """Resolve the result's column names: the schema if present, else the first row's keys.

    Args:
        result: The executed result.

    Returns:
        The column names in order, or `[]` when neither a schema nor any rows are present.
    """
    if result.schema_ is not None:
        return result.schema_.names
    if result.rows:
        return list(result.rows[0].keys())
    return []


def _hashable_key(value: Any) -> tuple[str, Any]:
    """Build a hashable duplicate-detection key, tagged to avoid value/repr collisions.

    Args:
        value: A cell value, possibly unhashable (e.g. a nested list/dict).

    Returns:
        `("val", value)` when `value` is hashable, else `("repr", repr(value))`.
    """
    try:
        hash(value)
    except TypeError:
        return ("repr", repr(value))
    return ("val", value)


def _render_key(key: tuple[str, Any]) -> str:
    """Render a duplicate key for display.

    Args:
        key: A key produced by `_hashable_key`.

    Returns:
        The repr of the underlying value (the surrogate repr is already a string).
    """
    tag, value = key
    return value if tag == "repr" else repr(value)
