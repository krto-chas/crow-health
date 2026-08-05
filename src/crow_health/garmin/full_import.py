from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from crow_health.importing import BatchImportReport, BatchImportService, ImportService
from crow_health.parsers.defaults import default_parser_registry
from crow_health.storage import JsonlObservationStore
from crow_health.validation import StoreValidationReport, validate_store


@dataclass(frozen=True, slots=True)
class GarminSleepImportReport:
    batch: BatchImportReport
    validation: StoreValidationReport

    @property
    def succeeded(self) -> bool:
        return self.batch.succeeded and self.validation.succeeded

    def to_dict(self) -> dict[str, Any]:
        return {
            "batch": asdict(self.batch),
            "validation": self.validation.to_dict(),
            "succeeded": self.succeeded,
        }


def run_garmin_sleep_import(
    archive: Path,
    store_path: Path,
    index_path: Path | None = None,
    *,
    patterns: tuple[str, ...] = ("*sleepData.json",),
) -> GarminSleepImportReport:
    importer = ImportService(
        default_parser_registry(),
        JsonlObservationStore(store_path),
    )
    batch = BatchImportService(importer).import_zip(archive, patterns=patterns)
    validation = validate_store(store_path, index_path, rebuild_index=True)
    return GarminSleepImportReport(batch=batch, validation=validation)
