from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from crow_health.evidence.models import Observation

JsonPayload = dict[str, Any] | list[Any]


@dataclass(frozen=True, slots=True)
class SourceDocument:
    evidence_id: str
    source_path: str
    media_type: str
    checksum: str
    payload: JsonPayload


@dataclass(frozen=True, slots=True)
class ParseMessage:
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class ParseResult:
    records: tuple[Observation, ...]
    warnings: tuple[ParseMessage, ...]
    errors: tuple[ParseMessage, ...]
    parser_name: str
    parser_version: str
    source_evidence_id: str

    @classmethod
    def success(
        cls,
        *,
        records: tuple[Observation, ...],
        parser_name: str,
        parser_version: str,
        source_evidence_id: str,
        warnings: tuple[ParseMessage, ...] = (),
    ) -> ParseResult:
        return cls(
            records=records,
            warnings=warnings,
            errors=(),
            parser_name=parser_name,
            parser_version=parser_version,
            source_evidence_id=source_evidence_id,
        )
