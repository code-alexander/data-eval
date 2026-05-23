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
uv run pytest                 # tests (add --cov=data_eval for coverage)
uv run ruff check && uv run ruff format --check
uv run ty check               # Astral typechecker
```
