test *args:
    uv run pytest {{args}}

test-cov *args:
    uv run coverage erase
    uv run coverage run -m pytest {{args}}
    uv run coverage combine
    uv run coverage report

lint:
    uv run ruff check
    uv run ruff format --check

typecheck:
    uv run --all-extras ty check src examples

check: lint typecheck test-cov
