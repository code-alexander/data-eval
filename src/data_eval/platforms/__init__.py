"""Platform adapters: per-platform integrations that execute SQL against a data platform."""

from data_eval.platforms.base import PlatformAdapter
from data_eval.platforms.duckdb import DuckDBAdapter
from data_eval.platforms.registry import duckdb_platform, postgres_platform, resolve

__all__ = ["DuckDBAdapter", "PlatformAdapter", "duckdb_platform", "postgres_platform", "resolve"]
