"""Result-set equivalence engine: column reconciliation plus the pure `build_result_set_diff` assembly seam."""

from data_eval.equivalence.columns import ColumnReconciliation, reconcile_columns
from data_eval.equivalence.compare import build_result_set_diff

__all__ = [
    "ColumnReconciliation",
    "build_result_set_diff",
    "reconcile_columns",
]
