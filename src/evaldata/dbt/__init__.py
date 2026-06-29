"""dbt integration: read a dbt project's artifacts into evaldata's types.

`DbtContext` normalises a built dbt `target/` (manifest.json + optional catalog.json) into
models, sources, and schema context for evaluating AI-generated SQL against the project.
"""

from evaldata.dbt.context import (
    Column,
    DbtContext,
    ModelRef,
    Relation,
    SchemaContext,
    SourceRef,
    TableSchema,
)
from evaldata.dbt.errors import DbtError

__all__ = [
    "Column",
    "DbtContext",
    "DbtError",
    "ModelRef",
    "Relation",
    "SchemaContext",
    "SourceRef",
    "TableSchema",
]
