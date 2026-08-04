from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class EvidenceFile:
    evidence_id: str
    source_name: str
    sha256: str
    size_bytes: int
    archived_path: str
    imported_at: datetime

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["imported_at"] = self.imported_at.isoformat()
        return value


@dataclass(frozen=True, slots=True)
class ImportJob:
    import_id: str
    source_evidence_id: str
    started_at: datetime
    status: str


@dataclass(frozen=True, slots=True)
class Observation:
    observation_id: str
    source_evidence_id: str
    source_path: str
    metric: str
    value: int | float | str | bool | None
    unit: str | None
    observed_at: datetime | None
    imported_at: datetime
    parser_name: str
    parser_version: str
