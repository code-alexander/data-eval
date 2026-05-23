"""Smoke test — the package imports."""

import data_eval


def test_package_imports() -> None:
    assert data_eval is not None
