# data-eval

## Comments

- Docstrings = public API docs (→ mkdocs): Google style (Args/Returns/Raises), single backticks, terse but complete.
- Inline comments: rare; only the non-obvious *why*. Never restate code; never reference other files (drifts).
- No baked-in rationale or external comparisons ("we chose X", "Typer recommends…", "same as dbt", "follows GE/pandas") in code — it rots and discourages future challenge. Put it in the commit/PR.
