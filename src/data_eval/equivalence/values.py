"""Cell-level value comparison: null equality and float tolerance."""

from typing import Any, Literal


def _is_numeric(x: Any) -> bool:
    """Check whether a value is numeric for tolerance comparison.

    Args:
        x: The value to test.

    Returns:
        `True` for `int` and `float` values, `False` for everything else — including
        `bool`, which subclasses `int` in Python.
    """
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def cells_equal(
    a: Any,
    b: Any,
    null_equality: Literal["equal", "distinct"],
    float_tolerance: float,
) -> bool:
    """Check whether two cell values are equal under the given null and float config.

    Args:
        a: The first cell value.
        b: The second cell value.
        null_equality: `"equal"` treats two NULLs as equal (SQL `IS NOT DISTINCT FROM`);
            `"distinct"` treats them as unequal (SQL `IS DISTINCT FROM`).
        float_tolerance: Absolute tolerance for numeric pairs.

    Returns:
        `True` if the values are equal. Numeric pairs (int/float, excluding bool) compare
        within `float_tolerance`; everything else falls through to Python `==`.
    """
    if a is None and b is None:
        return null_equality == "equal"
    if a is None or b is None:
        return False
    if _is_numeric(a) and _is_numeric(b):
        return abs(a - b) <= float_tolerance
    return a == b
