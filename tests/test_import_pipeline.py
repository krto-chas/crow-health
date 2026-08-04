from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from zipfile import ZipFile

from crow_health.evidence.models import Observation
from crow_health.importing import ImportService, load_json_zip_member
from crow_health.parsers.models import ParseMessage, ParseResult, SourceDocument
from crow_health.parsers.registry import ParserRegistry
from crow_health.storage import JsonlObservationStore


class StubParser:
    name = "stub"
    version = "1"
    supported_path_patterns: tuple[str, ...] = ("*.json",)
    supported_media_types: tuple[str, ...] = ("application/json",)

    def __init__(self, *, errors: tuple[ParseMessage, ...] = ()) -> None:
        self._errors = errors

    def parse(self, document: SourceDocument) -> ParseResult:
        records = () if self._errors else (_observation(document),)
        return ParseResult(
            records=records,
            warnings=(),
            errors=self._errors,
            parser_name=self.name,
            parser_version=self.version,
            source_evidence_id=document.evidence_id,
        )


def _observation(document: SourceDocument) -> Observation:
    return Observation(
        observation_id="obs-1",
        source_evidence_id=document.evidence_id,
        source_path=document.source_path,
        metric="test.metric",
        value=1,
        unit="count",
        observed_at=datetime(2026, 8, 4, tzinfo=UTC),
        imported_at=datetime(2026, 8, 4, 8, tzinfo=UTC),
        parser_name="stub",
        parser_version="1",
    )


def _document() -> SourceDocument:
    return SourceDocument(
        evidence_id="evidence-1",
        source_path="sample.json",
        media_type="application/json",
        checksum="checksum-1",
        payload={"value": 1},
    )


def test_import_service_parses_and_persists(tmp_path: Path) -> None:
    store = JsonlObservationStore(tmp_path / "observations.jsonl")
    service = ImportService(ParserRegistry().register(StubParser()), store)

    report = service.import_document(_document())

    assert report.persisted is True
    assert report.parsed_records == 1
    assert report.inserted_records == 1
    assert report.existing_records == 0
    assert len(store.all()) == 1


def test_repeated_import_is_idempotent(tmp_path: Path) -> None:
    store = JsonlObservationStore(tmp_path / "observations.jsonl")
    service = ImportService(ParserRegistry().register(StubParser()), store)
    service.import_document(_document())

    report = service.import_document(_document())

    assert report.inserted_records == 0
    assert report.existing_records == 1


def test_parser_errors_prevent_persistence(tmp_path: Path) -> None:
    store = JsonlObservationStore(tmp_path / "observations.jsonl")
    parser = StubParser(errors=(ParseMessage(code="invalid", message="bad record"),))
    service = ImportService(ParserRegistry().register(parser), store)

    report = service.import_document(_document())

    assert report.persisted is False
    assert report.errors[0].code == "invalid"
    assert store.all() == ()


def test_missing_parser_is_reported(tmp_path: Path) -> None:
    service = ImportService(
        ParserRegistry(),
        JsonlObservationStore(tmp_path / "observations.jsonl"),
    )

    report = service.import_document(_document())

    assert report.persisted is False
    assert report.errors[0].code == "parser_not_found"


def test_load_json_zip_member_is_deterministic(tmp_path: Path) -> None:
    archive = tmp_path / "export.zip"
    with ZipFile(archive, "w") as handle:
        handle.writestr("data/sample.json", json.dumps([{"value": 1}]))

    first = load_json_zip_member(archive, "data/sample.json")
    second = load_json_zip_member(archive, "data/sample.json")

    assert first == second
    assert first.evidence_id == first.checksum
    assert first.payload == [{"value": 1}]
