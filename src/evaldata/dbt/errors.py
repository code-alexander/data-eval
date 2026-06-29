"""Failure types for dbt artifact loading."""

from typing import Literal

from evaldata.types import Error

DbtErrorKind = Literal[
    "target_not_found",
    "artifact_invalid",
    "unsupported_schema_version",
    "golds_not_found",
    "golds_invalid",
    "profile_not_found",
    "unsupported_adapter",
]


class DbtError(Error):
    """A failure from loading a dbt project for evaluation.

    `kind` classifies the failure: `target_not_found` (no `manifest.json` in the directory),
    `artifact_invalid` (an artifact is unreadable or malformed), `unsupported_schema_version`
    (the manifest schema version is too old to read), `golds_not_found` / `golds_invalid` (the
    gold-cases file is missing or malformed), `profile_not_found` (no resolvable dbt profile),
    and `unsupported_adapter` (the profile's warehouse type has no evaldata platform).
    """

    kind: DbtErrorKind
