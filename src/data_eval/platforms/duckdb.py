"""`DuckDBAdapter`: in-process DuckDB execution backend."""

import time
from types import TracebackType
from typing import Self

import duckdb

from data_eval.types import Column, ExecutionResult


class DuckDBAdapter:
    """Executes SQL against an in-process DuckDB database."""

    def __init__(self, database: str = ":memory:") -> None:
        """Open a DuckDB connection to `database` (default `:memory:`)."""
        self._conn = duckdb.connect(database)

    def close(self) -> None:
        """Release the underlying DuckDB connection (file handle / WAL lock).

        Explicit close matters on Windows, where WAL locks make implicit cleanup unreliable.
        """
        self._conn.close()

    def __enter__(self) -> Self:
        """Return self; the connection is already open from `__init__`."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Close the underlying connection on context-manager exit."""
        self.close()

    def execute(self, sql: str) -> ExecutionResult:
        """Execute one SQL statement against the database.

        Args:
            sql: The SQL statement to execute.

        Returns:
            An `ExecutionResult` with the returned rows, schema, and latency. Query
            failures are returned as `ExecutionResult.error` rather than raised.
        """
        start = time.perf_counter()
        try:
            cursor = self._conn.execute(sql)
            description = cursor.description or []
            rows_raw = cursor.fetchall()
        except duckdb.Error as e:
            elapsed = time.perf_counter() - start
            return ExecutionResult(
                rows=[],
                schema=None,
                latency_seconds=elapsed,
                error=str(e),
            )
        elapsed = time.perf_counter() - start
        schema: list[Column] = []
        names: list[str] = []
        for name, type_, *_ in description:
            schema.append(Column(name=name, type=str(type_)))
            names.append(name)
        rows = [dict(zip(names, row, strict=True)) for row in rows_raw]
        return ExecutionResult(rows=rows, schema=schema, latency_seconds=elapsed)
