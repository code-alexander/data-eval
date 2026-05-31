"""Result-set equivalence engine: a pure `compare()` that every result-comparing scorer wraps."""

from data_eval.equivalence.compare import compare
from data_eval.equivalence.resultset import TypedResultSet, UntypedResultSet

__all__ = ["TypedResultSet", "UntypedResultSet", "compare"]
