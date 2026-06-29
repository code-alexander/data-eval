"""Build `EvalCase`s from a dbt project."""

from pathlib import Path
from typing import Annotated, Any, Literal, assert_never

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from evaldata.dbt._yaml import read_yaml
from evaldata.dbt.context import DbtContext
from evaldata.dbt.errors import DbtError
from evaldata.types import EvalCase, GoldQuery, PlatformRef

Mode = Literal["authored", "model"]


class _GoldCase(BaseModel):
    """One authored gold case from a golds file."""

    model_config = ConfigDict(extra="forbid")

    question: Annotated[str, Field(min_length=1)]
    gold_sql: Annotated[str, Field(min_length=1)]
    select: list[str] | None = None
    id: str | None = None


def load_dbt(
    target_dir: str | Path,
    *,
    platform: PlatformRef,
    golds: str | Path | None = None,
    mode: Mode = "authored",
) -> list[EvalCase] | DbtError:
    """Build eval cases from a built dbt project's artifacts.

    The schema context for each case is the project's tables (sources and models) rendered as
    `CREATE TABLE` statements into `metadata["schema_ddl"]`, ready for a schema-aware solver.

    In `authored` mode (the default), `golds` is a YAML/JSON file of `{question, gold_sql,
    select?, id?}` entries; `select` scopes the schema context to named tables. In `model` mode,
    each documented, compiled model becomes a case whose question is the model's description and
    whose gold query is the model's compiled SQL.

    Args:
        target_dir: A dbt `target/` directory holding `manifest.json` (and optionally
            `catalog.json`).
        platform: The warehouse the project is built in; every case runs against it.
        golds: Path to the gold-cases file (required for `authored` mode; ignored for `model`).
        mode: `authored` to read `golds`, or `model` to derive cases from documented models.

    Returns:
        The eval cases, or a `DbtError` if the artifacts, golds, or mode inputs cannot be read.
    """
    context = DbtContext.from_target_dir(target_dir)
    if isinstance(context, DbtError):
        return context
    match mode:
        case "authored":
            return _authored_cases(context, platform, golds)
        case "model":
            return _model_cases(context, platform)
        case _ as unreachable:  # pragma: no cover - exhaustiveness guard
            assert_never(unreachable)


def _authored_cases(context: DbtContext, platform: PlatformRef, golds: str | Path | None) -> list[EvalCase] | DbtError:
    if golds is None:
        return DbtError(kind="golds_not_found", message="authored mode requires a golds file")
    raw = read_yaml(Path(golds), not_found="golds_not_found", invalid="golds_invalid")
    if isinstance(raw, DbtError):
        return raw
    if not isinstance(raw, list):
        return DbtError(kind="golds_invalid", message=f"{golds} must be a list of gold cases")

    cases: list[EvalCase] = []
    for index, entry in enumerate(raw):
        try:
            gold = _GoldCase.model_validate(entry)
        except ValidationError as e:
            return DbtError(kind="golds_invalid", message=f"gold case {index} is invalid: {e}", cause=e)
        cases.append(
            EvalCase(
                id=gold.id or f"dbt/authored/{index}",
                input=gold.question,
                expected=GoldQuery(sql=gold.gold_sql),
                platform=platform,
                metadata=_metadata(context.schema_context(select=gold.select).as_text()),
            )
        )
    return cases


def _model_cases(context: DbtContext, platform: PlatformRef) -> list[EvalCase]:
    schema_ddl = context.schema_context().as_text()
    cases: list[EvalCase] = []
    for model in context.models():
        if not model.description or not model.compiled_sql:
            continue
        cases.append(
            EvalCase(
                id=f"dbt/model/{model.name}",
                input=model.description,
                expected=GoldQuery(sql=model.compiled_sql),
                platform=platform,
                metadata=_metadata(schema_ddl, model=model.name),
            )
        )
    return cases


def _metadata(schema_ddl: str, *, model: str | None = None) -> dict[str, Any]:
    metadata: dict[str, Any] = {"source": "dbt", "schema_ddl": schema_ddl}
    if model is not None:
        metadata["model"] = model
    return metadata
