from pathlib import Path

import pytest

from crow_health.apple_health import (
    APPLE_HEALTH_COVERAGE_SCHEMA,
    AppleHealthCoverageService,
    AppleHealthManifestEntry,
    AppleHealthSupport,
    load_manifest,
)


def entry(
    identifier: str,
    *,
    source_name: str = "Garmin Connect",
    source_bundle_id: str = "com.garmin.connect.mobile",
    units: tuple[str, ...] = (),
) -> AppleHealthManifestEntry:
    return AppleHealthManifestEntry(
        identifier=identifier,
        source_bundle_id=source_bundle_id,
        source_name=source_name,
        sample_count=3,
        earliest_sample="2026-08-01T00:00:00Z",
        latest_sample="2026-08-03T00:00:00Z",
        observed_units=units,
    )


def test_builds_deterministic_source_aware_coverage() -> None:
    report = AppleHealthCoverageService().build(
        (
            entry("HKQuantityTypeIdentifierStepCount", units=("count",)),
            entry("HKCategoryTypeIdentifierSleepAnalysis"),
            entry("UnknownType", source_name="iPhone", source_bundle_id="com.apple.health"),
        )
    )

    assert report.schema_version == APPLE_HEALTH_COVERAGE_SCHEMA
    assert [item.identifier for item in report.entries] == [
        "HKCategoryTypeIdentifierSleepAnalysis",
        "HKQuantityTypeIdentifierStepCount",
        "UnknownType",
    ]
    assert report.supported_entry_count == 1
    assert report.partial_entry_count == 1
    assert report.unsupported_entry_count == 1
    assert report.garmin_source_entry_count == 2
    assert report.entries[1].crow_metric == "activity.steps"
    assert report.entries[1].unit_matches is True


def test_reports_unit_mismatch_without_conversion() -> None:
    report = AppleHealthCoverageService().build(
        (entry("HKQuantityTypeIdentifierBodyMass", units=("lb",)),)
    )

    item = report.entries[0]
    assert item.expected_unit == "kg"
    assert item.unit_matches is False


def test_manifest_loader_rejects_unknown_schema(tmp_path: Path) -> None:
    path = tmp_path / "manifest.json"
    path.write_text('{"schema_version":"other","entries":[]}', encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported"):
        load_manifest(path)


def test_manifest_loader_preserves_no_sample_values(tmp_path: Path) -> None:
    path = tmp_path / "manifest.json"
    path.write_text(
        """{
          "schema_version": "crow-health.apple-health-manifest.v1",
          "entries": [{
            "identifier": "HKQuantityTypeIdentifierHeartRate",
            "source_bundle_id": "com.garmin.connect.mobile",
            "source_name": "Garmin Connect",
            "sample_count": 10,
            "earliest_sample": "2026-08-01T00:00:00Z",
            "latest_sample": "2026-08-02T00:00:00Z",
            "observed_units": ["count/min", "count/min"]
          }]
        }""",
        encoding="utf-8",
    )

    items = load_manifest(path)

    assert len(items) == 1
    assert items[0].observed_units == ("count/min",)
    report = AppleHealthCoverageService().build(items)
    assert report.entries[0].support is AppleHealthSupport.SUPPORTED
