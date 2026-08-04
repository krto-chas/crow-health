from __future__ import annotations

from dataclasses import dataclass

from crow_health.parsers.models import ParseMessage, SourceDocument
from crow_health.parsers.registry import ParserRegistry
from crow_health.storage import ObservationStore, StoreResult


@dataclass(frozen=True, slots=True)
class ImportReport:
    source_evidence_id: str
    parser_name: str | None
    parser_version: str | None
    parsed_records: int
    inserted_records: int
    existing_records: int
    warnings: tuple[ParseMessage, ...]
    errors: tuple[ParseMessage, ...]

    @property
    def persisted(self) -> bool:
        return not self.errors and self.parser_name is not None


class ImportService:
    def __init__(self, registry: ParserRegistry, store: ObservationStore) -> None:
        self._registry = registry
        self._store = store

    def import_document(self, document: SourceDocument) -> ImportReport:
        parsed = self._registry.parse(document)
        if parsed is None:
            return ImportReport(
                source_evidence_id=document.evidence_id,
                parser_name=None,
                parser_version=None,
                parsed_records=0,
                inserted_records=0,
                existing_records=0,
                warnings=(),
                errors=(
                    ParseMessage(
                        code="parser_not_found",
                        message=f"No parser matches {document.source_path}",
                    ),
                ),
            )

        if parsed.errors:
            return ImportReport(
                source_evidence_id=document.evidence_id,
                parser_name=parsed.parser_name,
                parser_version=parsed.parser_version,
                parsed_records=len(parsed.records),
                inserted_records=0,
                existing_records=0,
                warnings=parsed.warnings,
                errors=parsed.errors,
            )

        stored: StoreResult = self._store.append(parsed.records)
        return ImportReport(
            source_evidence_id=document.evidence_id,
            parser_name=parsed.parser_name,
            parser_version=parsed.parser_version,
            parsed_records=len(parsed.records),
            inserted_records=stored.inserted,
            existing_records=stored.existing,
            warnings=parsed.warnings,
            errors=(),
        )
