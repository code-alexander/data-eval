"""Platform-reference builders and ``PlatformRef`` -> live ``PlatformAdapter`` resolution.

Two responsibilities, both driver-light:

1. **Ref builders** (``duckdb_platform`` / ``postgres_platform``): construct a
   serializable ``PlatformRef`` from ergonomic keyword args. These do NOT touch a
   driver — building a reference must work without the platform's extra installed.

2. **Resolution** (``resolve``): turn a ``PlatformRef`` into a live adapter. Dispatch is
   an exhaustive ``match`` over ``PlatformKind`` (``_build``) — explicit dispatch, no
   inheritance, no base class, no MRO. Because ``PlatformKind`` lists only supported
   platforms, ``assert_never`` makes the ``match`` exhaustively type-checked: adding a
   platform fails ty until ``_build`` handles it. Each builder reads only the config keys
   its adapter needs and lazy-imports any optional driver, so importing this module never
   requires psycopg.

Lifecycle (best practice borrowed from dbt's process-global adapter factory and
pytest-postgresql's session-scoped server fixture): resolved adapters are cached in a
session-global ``_ADAPTERS`` map keyed by ``PlatformRef.name`` and reused across cases,
then closed once at session end via ``close_all`` (the pytest plugin's
``pytest_sessionfinish`` hook owns that call). An explicitly passed adapter still wins in
``assert_eval``; resolution is the fallback. Non-pytest callers own ``close_all`` themselves.
"""

from typing import assert_never

from data_eval.platforms.base import PlatformAdapter
from data_eval.platforms.duckdb import DuckDBAdapter
from data_eval.types import PlatformKind, PlatformRef


def duckdb_platform(name: str, path: str = ":memory:") -> PlatformRef:
    """Build a ``PlatformRef`` for an in-process DuckDB database at ``path``."""
    return PlatformRef(name=name, kind="duckdb", config={"path": path})


def postgres_platform(name: str, conninfo: str = "") -> PlatformRef:
    """Build a ``PlatformRef`` for a PostgreSQL database.

    ``conninfo`` is a libpq connection string (keyword/value or ``postgresql://`` URI);
    empty uses libpq defaults / ``PG*`` env vars. Building the ref needs no driver.
    """
    return PlatformRef(name=name, kind="postgres", config={"conninfo": conninfo})


def _build_duckdb(ref: PlatformRef) -> PlatformAdapter:
    return DuckDBAdapter(database=str(ref.config.get("path", ":memory:")))


def _build_postgres(ref: PlatformRef) -> PlatformAdapter:
    try:
        from data_eval.platforms.postgres import PostgresAdapter
    except ImportError as e:
        msg = "PostgresAdapter requires the 'postgres' extra; install it with `uv sync --extra postgres`"
        raise RuntimeError(msg) from e
    return PostgresAdapter(conninfo=str(ref.config.get("conninfo", "")))


def _build(ref: PlatformRef) -> PlatformAdapter:
    """Build a live adapter for ``ref`` by exhaustive dispatch over its kind."""
    kind: PlatformKind = ref.kind
    match kind:
        case "duckdb":
            return _build_duckdb(ref)
        case "postgres":
            return _build_postgres(ref)
        case _ as unreachable:  # pragma: no cover - exhaustiveness guard
            assert_never(unreachable)


# Session-global cache of live adapters, keyed by ``PlatformRef.name``. Owned by the
# pytest plugin, which closes everything via ``close_all`` at session end.
_ADAPTERS: dict[str, tuple[PlatformRef, PlatformAdapter]] = {}


def resolve(ref: PlatformRef) -> PlatformAdapter:
    """Return a live adapter for ``ref``, building and caching one on first use.

    Reuses the cached adapter on subsequent calls for the same ``ref.name``. Raises
    ``ValueError`` if the name is already bound to a different configuration. An unsupported
    ``kind`` is unrepresentable — ``PlatformRef`` validation rejects it before resolution.
    """
    cached = _ADAPTERS.get(ref.name)
    if cached is not None:
        cached_ref, adapter = cached
        if cached_ref != ref:
            msg = (
                f"platform name {ref.name!r} is already bound to a different configuration; "
                "platform names must uniquely identify a connection"
            )
            raise ValueError(msg)
        return adapter

    adapter = _build(ref)
    _ADAPTERS[ref.name] = (ref, adapter)
    return adapter


def close_all() -> None:
    """Close every cached adapter and clear the cache (idempotent; no-op when empty)."""
    for _ref, adapter in _ADAPTERS.values():
        close = getattr(adapter, "close", None)
        if callable(close):
            close()
    _ADAPTERS.clear()
