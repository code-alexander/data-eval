"""Reporting: render eval outcomes for humans (terminal) and machines (JUnit/JSON, later)."""

from data_eval.reporting.terminal import render_failure, render_solver_error

__all__ = ["render_failure", "render_solver_error"]
