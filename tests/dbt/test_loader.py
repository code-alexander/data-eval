"""Tests for building EvalCases from a dbt project."""

import textwrap
from pathlib import Path

import pytest

from evaldata.dbt.context import DbtContext, ModelRef, Relation
from evaldata.dbt.errors import DbtError
from evaldata.dbt.loader import _model_cases, load_dbt
from evaldata.platforms.registry import duckdb_platform
from evaldata.types import GoldQuery

pytestmark = pytest.mark.unit

ARTIFACTS = Path(__file__).parent / "fixtures" / "jaffle_duckdb" / "artifacts"
PLATFORM = duckdb_platform(name="dbt-test", path=":memory:")


def _golds(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "golds.yml"
    path.write_text(textwrap.dedent(body), encoding="utf-8")
    return path


def test_authored_cases(tmp_path: Path) -> None:
    golds = _golds(
        tmp_path,
        """
        - question: How many customers?
          gold_sql: select count(*) from customers
          select: [customers]
          id: count-customers
        - question: List orders
          gold_sql: select * from stg_orders
        """,
    )
    cases = load_dbt(ARTIFACTS, platform=PLATFORM, golds=golds)
    assert not isinstance(cases, DbtError)
    assert [c.id for c in cases] == ["count-customers", "dbt/authored/1"]

    first = cases[0]
    assert first.input == "How many customers?"
    assert isinstance(first.expected, GoldQuery)
    assert first.expected.sql == "select count(*) from customers"
    assert first.platform is PLATFORM
    assert first.metadata["source"] == "dbt"
    assert "model" not in first.metadata
    assert 'CREATE TABLE "jaffle"."main"."customers"' in first.metadata["schema_ddl"]
    assert "raw_customers" not in first.metadata["schema_ddl"]
    assert "raw_customers" in cases[1].metadata["schema_ddl"]


def test_model_mode(tmp_path: Path) -> None:
    cases = load_dbt(ARTIFACTS, platform=PLATFORM, mode="model")
    assert not isinstance(cases, DbtError)
    assert [c.id for c in cases] == ["dbt/model/stg_customers", "dbt/model/stg_orders", "dbt/model/customers"]
    customers = cases[-1]
    assert customers.input == "Customer dimension enriched with order activity."
    assert isinstance(customers.expected, GoldQuery)
    assert "select" in customers.expected.sql.lower()
    assert customers.metadata["model"] == "customers"
    assert customers.metadata["source"] == "dbt"


def test_bad_target_dir(tmp_path: Path) -> None:
    result = load_dbt(tmp_path, platform=PLATFORM, mode="model")
    assert isinstance(result, DbtError)
    assert result.kind == "target_not_found"


def test_authored_requires_golds() -> None:
    result = load_dbt(ARTIFACTS, platform=PLATFORM)
    assert isinstance(result, DbtError)
    assert result.kind == "golds_not_found"


def test_golds_file_missing(tmp_path: Path) -> None:
    result = load_dbt(ARTIFACTS, platform=PLATFORM, golds=tmp_path / "nope.yml")
    assert isinstance(result, DbtError)
    assert result.kind == "golds_not_found"


def test_golds_not_a_list(tmp_path: Path) -> None:
    result = load_dbt(ARTIFACTS, platform=PLATFORM, golds=_golds(tmp_path, "question: x\n"))
    assert isinstance(result, DbtError)
    assert result.kind == "golds_invalid"


def test_golds_invalid_entry(tmp_path: Path) -> None:
    result = load_dbt(ARTIFACTS, platform=PLATFORM, golds=_golds(tmp_path, "- question: no sql here\n"))
    assert isinstance(result, DbtError)
    assert result.kind == "golds_invalid"


def test_malformed_golds_yaml(tmp_path: Path) -> None:
    result = load_dbt(ARTIFACTS, platform=PLATFORM, golds=_golds(tmp_path, "- question: [unclosed\n"))
    assert isinstance(result, DbtError)
    assert result.kind == "golds_invalid"


def test_model_mode_skips_undocumented_or_uncompiled() -> None:
    relation = Relation("db", "sc", "m", '"db"."sc"."m"')
    documented = ModelRef("m1", "model.x.m1", relation, "select 1", "documented", ())
    no_description = ModelRef("m2", "model.x.m2", relation, "select 2", None, ())
    no_compiled_sql = ModelRef("m3", "model.x.m3", relation, None, "documented but not compiled", ())
    context = DbtContext(models=[documented, no_description, no_compiled_sql], sources=[], schema_version="v12")

    cases = _model_cases(context, PLATFORM)
    assert [c.id for c in cases] == ["dbt/model/m1"]
