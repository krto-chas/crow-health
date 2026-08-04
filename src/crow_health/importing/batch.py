from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from zipfile import ZipFile

from crow_health.importing.pipeline import ImportReport, ImportService
from crow_health.importing.sources import load_json_zip_member
from crow_health.parsers.models import ParseMessage


@dataclass(frozen=True, slots=True)
class BatchMemberReport:
    member_path: str
    report: ImportReport | None
    errors: tuple[ParseMessage, ...] = ()

    @property
    def succeeded(self) -> bool:
        return self.report is not None and self.report.persisted and not self.errors


@dataclass(frozen=True, slots=True)
class BatchImportReport:
    archive: str
    matched_members: int
    completed_members: int
    failed_members: int
    parsed_records: int
    inserted_records: int
    existing_records: int
    members: tuple[BatchMemberReport, ...]

    @property
    def succeeded(self) -> bool:
        return self.matched_members > 0 and self.failed_members == 0


def discover_zip_members(archive: Path, patterns: tuple[str, ...]) -> tuple[str, ...]:
    with ZipFile(archive) as handle:
        members = (
            item.filename
            for item in handle.infolist()
            if not item.is_dir() and any(fnmatch(item.filename, pattern) for pattern in patterns)
        )
    return tuple(sorted(members))


class BatchImportService:
    def __init__(self, importer: ImportService) -> None:
        self._importer = importer

    def import_zip(
        self,
        archive: Path,
        *,
        patterns: tuple[str, ...],
    ) -> BatchImportReport:
        member_paths = discover_zip_members(archive, patterns)
        reports: list[BatchMemberReport] = []

        for member_path in member_paths:
            try:
                document = load_json_zip_member(archive, member_path)
                report = self._importer.import_document(document)
            except (FileNotFoundError, TypeError, ValueError) as exc:
                reports.append(
                    BatchMemberReport(
                        member_path=member_path,
                        report=None,
                        errors=(
                            ParseMessage(
                                code="source_error",
                                message=str(exc),
                            ),
                        ),
                    )
                )
                continue

            reports.append(BatchMemberReport(member_path=member_path, report=report))

        completed = sum(item.succeeded for item in reports)
        failed = len(reports) - completed
        return BatchImportReport(
            archive=str(archive),
            matched_members=len(member_paths),
            completed_members=completed,
            failed_members=failed,
            parsed_records=sum(
                item.report.parsed_records for item in reports if item.report is not None
            ),
            inserted_records=sum(
                item.report.inserted_records for item in reports if item.report is not None
            ),
            existing_records=sum(
                item.report.existing_records for item in reports if item.report is not None
            ),
            members=tuple(reports),
        )
