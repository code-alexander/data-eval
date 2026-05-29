"""Conformance plumbing: ``ConformanceFixtures`` Protocol, per-adapter fixture types, parametrised ``under_test`` fixture.

Pattern (b): each adapter contributes its OWN named ``*Fixtures`` dataclass whose values
are the dialect-specific SQL strings it uses to exercise each behavioural test. The
``ConformanceFixtures`` Protocol names the shared vocabulary; static checkers verify
each adapter's dataclass satisfies it. No inheritance, no MRO, no defaults overridden
by descendants — each adapter's complete SQL surface is one local literal.

Adding a new adapter = add one ``*Fixtures`` dataclass + one factory + one entry in
``params=[...]`` / ``ids=[...]``. Adding a new behavioural test = add one field to the
Protocol + one field to every concrete fixtures dataclass (compile-time enforcement of
coverage via the dataclass constructor).
"""

from dataclasses import dataclass
from typing import Protocol

import pytest

from data_eval.platforms.base import PlatformAdapter
from data_eval.platforms.duckdb import DuckDBAdapter


class ConformanceFixtures(Protocol):
    """The shared vocabulary of SQL fragments every adapter must supply.

    Each attribute names a *behaviour*; its value is the adapter's dialect-specific
    SQL that exercises it. Adapters implement this Protocol structurally via their
    own concrete ``@dataclass(frozen=True)`` types — no inheritance.
    """

    one_row_one_column: str  # returns one row with one column named "n"
    empty_result: str  # returns zero rows with a known schema (column "n")
    three_rows: str  # returns three rows in column "n" with values 1, 2, 3
    null_value: str  # returns one row with NULL in column "x"
    references_missing_table: str  # references a non-existent table
    parse_error: str  # is syntactically invalid


@dataclass(frozen=True)
class DuckDBFixtures:
    """DuckDB's concrete ``ConformanceFixtures`` — structurally satisfies the Protocol."""

    one_row_one_column: str = "SELECT 1 AS n"
    empty_result: str = "SELECT 1 AS n WHERE 1=0"
    three_rows: str = "SELECT 1 AS n UNION ALL SELECT 2 UNION ALL SELECT 3"
    null_value: str = "SELECT NULL AS x"
    references_missing_table: str = "SELECT * FROM does_not_exist_xyz"
    parse_error: str = "SELECT FROM nope"


@dataclass(frozen=True)
class UnderTest:
    """One adapter-under-test: its live ``PlatformAdapter`` + the SQL it uses."""

    adapter: PlatformAdapter
    fixtures: ConformanceFixtures


def _duckdb_under_test() -> UnderTest:
    return UnderTest(adapter=DuckDBAdapter(), fixtures=DuckDBFixtures())


# Function-scoped: each test gets a fresh adapter. Cheap for DuckDB (:memory:);
# revisit when remote adapters (Postgres, Snowflake) arrive and connect cost
# starts to matter — switch to session-scope with per-test isolation as needed.
@pytest.fixture(
    params=[
        pytest.param(_duckdb_under_test, id="duckdb", marks=pytest.mark.unit),
    ],
)
def under_test(request: pytest.FixtureRequest) -> UnderTest:
    """Return one (adapter, fixtures) pair; parametrised across all registered adapters."""
    factory = request.param
    return factory()
