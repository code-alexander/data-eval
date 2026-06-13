# data-eval

AI evals framework for data & analytics engineering teams.

> Status: pre-alpha. The API will change.

## Install (once published)

```bash
uv add data-eval                              # core
uv add "data-eval[snowflake]"                 # + Snowflake adapter
uv add "data-eval[all-platforms,litellm]"     # everything
```

## Develop locally

```bash
git clone https://github.com/code-alexander/data-eval.git
cd data-eval
uv sync                       # core + dev tooling
uv run pre-commit install
just check                    # lint + typecheck + tests with coverage (runs everything)
```

`just check` runs `just lint` (`ruff check` + `ruff format --check`), `just typecheck`
(`uv run --all-extras ty check src examples`), and `just test-cov` (tests with accurate
coverage, held at 100%). Run them individually as needed.

### Platform e2e tests

Adapter conformance for real platforms is marked `e2e` and skips when the platform
isn't reachable, so the default `uv run pytest` is green without one. To run the
Postgres suite locally:

```bash
docker compose up -d                  # postgres:17 on localhost:5432
uv run --extra postgres pytest -m e2e # connection via POSTGRES_TEST_* env (defaults match compose)
```
