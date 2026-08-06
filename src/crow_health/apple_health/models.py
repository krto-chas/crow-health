from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any


class AppleHealthSupport(StrEnum):
    SUPPORTED = "supported"
    PARTIAL = "partial"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True, slots=True)
class AppleHealthTypeDefinition:
    identifier: str
    crow_metric: str | None
    support: AppleHealthSupport
    expected_unit: str | None
    notes: str


@dataclass(frozen=True, slots=True)
class AppleHealthManifestEntry:
    identifier: str
    source_bundle_id: str
    source_name: str
    sample_count: int
    earliest_sample: str | None
    latest_sample: str | None
    observed_units: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AppleHealthCoverageEntry:
    identifier: str
    crow_metric: str | None
    support: AppleHealthSupport
    source_bundle_id: str
    source_name: str
    sample_count: int
    earliest_sample: str | None
    latest_sample: str | None
    observed_units: tuple[str, ...]
    expected_unit: str | None
    unit_matches: bool | None
    notes: str


@dataclass(frozen=True, slots=True)
class AppleHealthCoverageReport:
    schema_version: str
    entries: tuple[AppleHealthCoverageEntry, ...]
    supported_entry_count: int
    partial_entry_count: int
    unsupported_entry_count: int
    garmin_source_entry_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
