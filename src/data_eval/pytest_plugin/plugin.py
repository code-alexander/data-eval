"""The data-eval pytest plugin: the `case` fixture, run summary, and JSON artifact."""

from pathlib import Path

import pytest

from data_eval.loaders.python import read_eval_case
from data_eval.platforms.registry import close_all
from data_eval.reporting.collector import reports, run_report_json
from data_eval.reporting.terminal import render_summary
from data_eval.types import EvalCase

_JSON_OPTION = "--data-eval-json"


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register `--data-eval-json=PATH` to write the structured results artifact."""
    group = parser.getgroup("data-eval")
    group.addoption(
        _JSON_OPTION,
        action="store",
        default=None,
        metavar="PATH",
        help="Write a structured data-eval results JSON artifact to PATH.",
    )


@pytest.fixture
def case(request: pytest.FixtureRequest) -> EvalCase:
    """Inject the `EvalCase` attached by `@eval_case` on the requesting test function.

    Args:
        request: The pytest fixture request, used to find the requesting test function.

    Returns:
        The `EvalCase` attached to the test by its `@eval_case(...)` decorator.

    Raises:
        UsageError: If the requesting test is not decorated with `@eval_case(...)`.
    """
    evalcase = read_eval_case(request.function)
    if evalcase is None:
        msg = (
            f"test {request.function.__name__!r} requests the 'case' fixture but is not decorated with @eval_case(...)"
        )
        raise pytest.UsageError(msg)
    return evalcase


def pytest_terminal_summary(
    terminalreporter: pytest.TerminalReporter,
    exitstatus: int,
    config: pytest.Config,
) -> None:
    """Print the data-eval run summary table (controller only; skipped when no case ran)."""
    if hasattr(config, "workerinput"):  # xdist worker — the controller reports
        return
    case_reports = reports()
    if not case_reports:
        return
    terminalreporter.write_sep("=", "data-eval summary")
    for line in render_summary(case_reports).splitlines():
        terminalreporter.write_line(line)


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Close resolved adapters and, if requested, write the JSON results artifact."""
    close_all()
    if hasattr(session.config, "workerinput"):  # xdist worker — the controller writes
        return
    path = session.config.getoption(_JSON_OPTION)
    if path is not None:
        Path(path).write_text(run_report_json(reports()))
