"""Tests for `ExpectationSuiteScorer` — evaluates an `ExpectationSuite` against a result."""

import pytest

from data_eval.scorers import ExpectationSuiteScorer, Scorer
from data_eval.scorers.expectation_suite import SCORER_NAME
from data_eval.types import (
    Column,
    ColumnPresenceExpectation,
    ColumnTypeExpectation,
    EvalCase,
    ExecutionResult,
    ExpectationSuite,
    Expected,
    ExpectedSQL,
    NotNullExpectation,
    PlatformRef,
    RowCountExpectation,
    SolverOutput,
    SqlType,
    UniqueExpectation,
)

_OUTPUT = SolverOutput(output="SELECT ...")


def _case(expected: Expected) -> EvalCase:
    return EvalCase(
        id="c",
        input="q",
        expected=expected,
        platform=PlatformRef(name="x", kind="duckdb"),
    )


def _suite(*expectations: object) -> EvalCase:
    return _case(ExpectationSuite(expectations=list(expectations)))


@pytest.mark.unit
class TestRowCount:
    def test_pass(self) -> None:
        case = _suite(RowCountExpectation(exact=2))
        result = ExecutionResult(rows=[{"n": 1}, {"n": 2}], latency_seconds=0.0)
        score = ExpectationSuiteScorer().score(case, _OUTPUT, result)
        assert score.scorer == SCORER_NAME
        assert score.passed is True
        assert score.explanation is None

    def test_fail(self) -> None:
        case = _suite(RowCountExpectation(exact=5))
        result = ExecutionResult(rows=[{"n": 1}], latency_seconds=0.0)
        score = ExpectationSuiteScorer().score(case, _OUTPUT, result)
        assert score.passed is False
        assert score.explanation is not None
        assert "expected 5 rows, got 1" in score.explanation


@pytest.mark.unit
class TestColumnPresence:
    def test_pass_from_schema(self) -> None:
        case = _suite(ColumnPresenceExpectation(columns=["id", "name"]))
        result = ExecutionResult(
            rows=[],
            schema=[Column(name="id", type="BIGINT"), Column(name="name", type="VARCHAR")],
            latency_seconds=0.0,
        )
        assert ExpectationSuiteScorer().score(case, _OUTPUT, result).passed is True

    def test_pass_from_rows_when_no_schema(self) -> None:
        case = _suite(ColumnPresenceExpectation(columns=["id"]))
        result = ExecutionResult(rows=[{"id": 1, "name": "x"}], latency_seconds=0.0)
        assert ExpectationSuiteScorer().score(case, _OUTPUT, result).passed is True

    def test_fail_lists_missing(self) -> None:
        case = _suite(ColumnPresenceExpectation(columns=["id", "missing"]))
        result = ExecutionResult(rows=[{"id": 1}], latency_seconds=0.0)
        score = ExpectationSuiteScorer().score(case, _OUTPUT, result)
        assert score.passed is False
        assert score.explanation is not None
        assert "missing" in score.explanation

    def test_fail_when_no_schema_and_no_rows(self) -> None:
        # A non-row-returning result (no schema, no rows) exposes no columns, so any
        # expected column is reported missing.
        case = _suite(ColumnPresenceExpectation(columns=["id"]))
        result = ExecutionResult(rows=[], latency_seconds=0.0)
        score = ExpectationSuiteScorer().score(case, _OUTPUT, result)
        assert score.passed is False
        assert score.explanation is not None
        assert "id" in score.explanation


@pytest.mark.unit
class TestColumnType:
    def test_pass(self) -> None:
        case = _suite(ColumnTypeExpectation(column="n", expected_type="BIGINT"))
        result = ExecutionResult(
            rows=[{"n": 1}],
            schema=[Column(name="n", type=SqlType.parse("BIGINT", "duckdb"))],
            latency_seconds=0.0,
        )
        assert ExpectationSuiteScorer().score(case, _OUTPUT, result).passed is True

    def test_pass_aliased_type(self) -> None:
        # INT8 and BIGINT canonicalise to the same duckdb type.
        case = _suite(ColumnTypeExpectation(column="n", expected_type="INT8"))
        result = ExecutionResult(
            rows=[{"n": 1}],
            schema=[Column(name="n", type=SqlType.parse("BIGINT", "duckdb"))],
            latency_seconds=0.0,
        )
        assert ExpectationSuiteScorer().score(case, _OUTPUT, result).passed is True

    def test_fail_mismatch(self) -> None:
        case = _suite(ColumnTypeExpectation(column="n", expected_type="INTEGER"))
        result = ExecutionResult(
            rows=[{"n": 1}],
            schema=[Column(name="n", type=SqlType.parse("BIGINT", "duckdb"))],
            latency_seconds=0.0,
        )
        score = ExpectationSuiteScorer().score(case, _OUTPUT, result)
        assert score.passed is False
        assert score.explanation is not None
        assert "column_type" in score.explanation

    def test_fail_absent_column(self) -> None:
        case = _suite(ColumnTypeExpectation(column="missing", expected_type="BIGINT"))
        result = ExecutionResult(
            rows=[{"n": 1}],
            schema=[Column(name="n", type=SqlType.parse("BIGINT", "duckdb"))],
            latency_seconds=0.0,
        )
        score = ExpectationSuiteScorer().score(case, _OUTPUT, result)
        assert score.passed is False
        assert score.explanation is not None
        assert "not found" in score.explanation

    def test_fail_no_schema(self) -> None:
        case = _suite(ColumnTypeExpectation(column="n", expected_type="BIGINT"))
        result = ExecutionResult(rows=[{"n": 1}], latency_seconds=0.0)
        score = ExpectationSuiteScorer().score(case, _OUTPUT, result)
        assert score.passed is False
        assert score.explanation is not None
        assert "no column schema available" in score.explanation


@pytest.mark.unit
class TestNotNull:
    def test_pass(self) -> None:
        case = _suite(NotNullExpectation(column="email"))
        result = ExecutionResult(rows=[{"email": "a"}, {"email": "b"}], latency_seconds=0.0)
        assert ExpectationSuiteScorer().score(case, _OUTPUT, result).passed is True

    def test_pass_zero_rows(self) -> None:
        case = _suite(NotNullExpectation(column="email"))
        result = ExecutionResult(rows=[], schema=[Column(name="email", type="VARCHAR")], latency_seconds=0.0)
        assert ExpectationSuiteScorer().score(case, _OUTPUT, result).passed is True

    def test_fail_reports_count(self) -> None:
        case = _suite(NotNullExpectation(column="email"))
        result = ExecutionResult(
            rows=[{"email": "a"}, {"email": None}, {"email": None}],
            latency_seconds=0.0,
        )
        score = ExpectationSuiteScorer().score(case, _OUTPUT, result)
        assert score.passed is False
        assert score.explanation is not None
        assert "2 NULL value(s)" in score.explanation

    def test_fail_absent_column(self) -> None:
        case = _suite(NotNullExpectation(column="email"))
        result = ExecutionResult(rows=[{"id": 1}], latency_seconds=0.0)
        score = ExpectationSuiteScorer().score(case, _OUTPUT, result)
        assert score.passed is False
        assert score.explanation is not None
        assert "not found" in score.explanation


@pytest.mark.unit
class TestUnique:
    def test_pass(self) -> None:
        case = _suite(UniqueExpectation(column="id"))
        result = ExecutionResult(rows=[{"id": 1}, {"id": 2}], latency_seconds=0.0)
        assert ExpectationSuiteScorer().score(case, _OUTPUT, result).passed is True

    def test_fail_duplicate(self) -> None:
        case = _suite(UniqueExpectation(column="id"))
        result = ExecutionResult(rows=[{"id": 1}, {"id": 1}], latency_seconds=0.0)
        score = ExpectationSuiteScorer().score(case, _OUTPUT, result)
        assert score.passed is False
        assert score.explanation is not None
        assert "duplicated value(s)" in score.explanation

    def test_fail_null_duplicates(self) -> None:
        # dbt semantics: NULLs compare as equal, so two NULLs are a duplicate.
        case = _suite(UniqueExpectation(column="id"))
        result = ExecutionResult(rows=[{"id": None}, {"id": None}], latency_seconds=0.0)
        assert ExpectationSuiteScorer().score(case, _OUTPUT, result).passed is False

    def test_unhashable_values_duplicate(self) -> None:
        case = _suite(UniqueExpectation(column="c"))
        result = ExecutionResult(rows=[{"c": [1, 2]}, {"c": [1, 2]}], latency_seconds=0.0)
        assert ExpectationSuiteScorer().score(case, _OUTPUT, result).passed is False

    def test_unhashable_values_distinct(self) -> None:
        case = _suite(UniqueExpectation(column="c"))
        result = ExecutionResult(rows=[{"c": [1]}, {"c": [2]}], latency_seconds=0.0)
        assert ExpectationSuiteScorer().score(case, _OUTPUT, result).passed is True

    def test_fail_absent_column(self) -> None:
        case = _suite(UniqueExpectation(column="id"))
        result = ExecutionResult(rows=[{"x": 1}], latency_seconds=0.0)
        score = ExpectationSuiteScorer().score(case, _OUTPUT, result)
        assert score.passed is False
        assert score.explanation is not None
        assert "not found" in score.explanation


@pytest.mark.unit
class TestSuiteAggregation:
    def test_execution_error_passthrough(self) -> None:
        case = _suite(RowCountExpectation(exact=1))
        result = ExecutionResult(rows=[], latency_seconds=0.0, error="boom")
        score = ExpectationSuiteScorer().score(case, _OUTPUT, result)
        assert score.passed is False
        assert score.diff is None
        assert score.explanation is not None
        assert "boom" in score.explanation

    def test_raises_on_non_expectation_suite(self) -> None:
        case = _case(ExpectedSQL(sql="SELECT 1"))
        result = ExecutionResult(rows=[{"n": 1}], latency_seconds=0.0)
        with pytest.raises(TypeError, match="ExpectationSuite"):
            ExpectationSuiteScorer().score(case, _OUTPUT, result)

    def test_aggregates_multiple_failures(self) -> None:
        case = _suite(RowCountExpectation(exact=5), NotNullExpectation(column="email"))
        result = ExecutionResult(rows=[{"email": None}], latency_seconds=0.0)
        score = ExpectationSuiteScorer().score(case, _OUTPUT, result)
        assert score.passed is False
        assert score.diff is None
        assert score.explanation is not None
        assert "2 expectation(s) failed" in score.explanation
        assert "row_count" in score.explanation
        assert "not_null" in score.explanation

    def test_all_pass(self) -> None:
        case = _suite(
            RowCountExpectation(exact=1),
            ColumnPresenceExpectation(columns=["id"]),
            UniqueExpectation(column="id"),
            NotNullExpectation(column="id"),
        )
        result = ExecutionResult(rows=[{"id": 1}], latency_seconds=0.0)
        score = ExpectationSuiteScorer().score(case, _OUTPUT, result)
        assert score.passed is True
        assert score.explanation is None

    def test_satisfies_scorer_protocol(self) -> None:
        assert isinstance(ExpectationSuiteScorer(), Scorer)
