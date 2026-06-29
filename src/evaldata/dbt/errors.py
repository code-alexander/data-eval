"""Failure types for dbt artifact loading."""

from typing import Literal

from evaldata.types import Error

DbtErrorKind = Literal["target_not_found", "artifact_invalid", "unsupported_schema_version"]


class DbtError(Error):
    """A failure from loading a dbt project's artifacts.

    `kind` classifies the failure: `target_not_found` when the directory has no `manifest.json`,
    `artifact_invalid` when an artifact is unreadable or malformed, and
    `unsupported_schema_version` when the manifest's schema version is too old to read.
    """

    kind: DbtErrorKind
