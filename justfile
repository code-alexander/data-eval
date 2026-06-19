test *args:
    uv run --all-extras pytest {{args}}

test-cov *args:
    uv run coverage erase
    uv run --all-extras coverage run -m pytest {{args}}
    uv run coverage combine
    uv run coverage report

# Run only `cloud` e2e (Databricks, …) in isolation; needs the secrets in the env.
test-cloud *args:
    uv run --all-extras pytest -m cloud {{args}}

lint:
    uv run ruff check
    uv run ruff format --check

fix:
    uv run ruff check --fix
    uv run ruff format

typecheck:
    uv run --all-extras ty check src examples

precommit:
    uv run pre-commit run --all-files --show-diff-on-failure

build:
    uv build

# Everyday gate: runs everything incl. `cloud` (needs credentials in the env); coverage 100%.
check: lint typecheck
    just test-cov

# Fast iteration: like `check` but skips `cloud`; no coverage gate. CI still runs everything.
check-nocloud: lint typecheck
    just test '-m "not cloud"'

ci: check build

release *args="auto":
    changie batch {{args}}
    changie merge
