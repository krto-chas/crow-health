from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from zipfile import ZipFile

from crow_health.evidence.models import Observation
from crow_health.importing import BatchImportService, ImportService, discover_zip_members
from crow_health.parsers.models import ParseMessage, ParseResult, SourceDocument
from crow_health.parsers.registry import ParserRegistry
from crow_health.storage import JsonlObservationStore


class StubParser:
    name = "stub"
    version = "1"
    supported_path_patterns: tuple[str, ...] = ("*sleepData.json",)
    supported_media_types: tuple[str, ...] = ("application/json",)

    def parse(self, document: SourceDocument) -> ParseResult:
        if document.payload == {"invalid": True}:
            return ParseResult(
                records=(),
                warnings=(),
                errors=(ParseMessage(code="invalid", message="invalid source"),),
                parser_name=self.name,
                parser_version=self.version,
                source_evidence_id=document.evidence_id,
            )
        observation = Observation(
            observation_id=f"obs-{document.evidence_id}",
            source_evidence_id=document.evidence_id,
            source_path=document.source_path,
            metric="test.metric",
            value=1,
            unit="count",
            observed_at=datetime(2026, 8, 4, tzinfo=UTC),
            imported_at=datetime(2026, 8, 4, 8, tzinfo=UTC),
            parser_name=self.name,
            parser_version=self.version,
        )
        return ParseResult.success(
            records=(observation,),
            parser_name=self.name,
            parser_version=self.version,
            source_evidence_id=document.evidence_id,
        )


def _archive(tmp_path: Path, members: dict[str, object]) -> Path:
    archive = tmp_path / "export.zip"
    with ZipFile(archive, "w") as handle:
        for path, payload in members.items():
            handle.writestr(path, json.dumps(payload))
    return archive


def _service(tmp_path: Path) -> BatchImportService:
    importer = ImportService(
        ParserRegistry().register(StubParser()),
        JsonlObservationStore(tmp_path / "observations.jsonl"),
    )
    return BatchImportService(importer)


def test_discovery_is_filtered_and_sorted(tmp_path: Path) -> None:
    archive = _archive(
        tmp_path,
        {
            "z_sleepData.json": [],
            "a_sleepData.json": [],
            "other.json": [],
        },
    )

    members = discover_zip_members(archive, ("*sleepData.json",))

    assert members == ("a_sleepData.json", "z_sleepData.json")


def test_batch_imports_all_matching_members(tmp_path: Path) -> None:
    archive = _archive(
        tmp_path,
        {
            "a_sleepData.json": [{"value": 1}],
            "b_sleepData.json": [{"value": 2}],
            "ignored.json": [{"value": 3}],
        },
    )

    report = _service(tmp_path).import_zip(archive, patterns=("*sleepData.json",))

    assert report.succeeded is True
    assert report.matched_members == 2
    assert report.completed_members == 2
    assert report.failed_members == 0
    assert report.inserted_records == 2


def test_repeated_batch_is_idempotent(tmp_path: Path) -> None:
    archive = _archive(tmp_path, {"a_sleepData.json": [{"value": 1}]})
    service = _service(tmp_path)
    service.import_zip(archive, patterns=("*sleepData.json",))

    report = service.import_zip(archive, patterns=("*sleepData.json",))

    assert report.inserted_records == 0
    assert report.existing_records == 1


def test_failed_member_does_not_stop_other_members(tmp_path: Path) -> None:
    archive = _archive(
        tmp_path,
        {
            "a_sleepData.json": {"invalid": True},
            "b_sleepData.json": [{"value": 2}],
        },
    )

    report = _service(tmp_path).import_zip(archive, patterns=("*sleepData.json",))

    assert report.succeeded is False
    assert report.completed_members == 1
    assert report.failed_members == 1
    assert report.inserted_records == 1


def test_empty_match_is_not_success(tmp_path: Path) -> None:
    archive = _archive(tmp_path, {"other.json": []})

    report = _service(tmp_path).import_zip(archive, patterns=("*sleepData.json",))

    assert report.succeeded is False
    assert report.matched_members == 0
