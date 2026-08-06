from pathlib import Path

import pytest

from crow_health.apple_health.intake import AppleHealthManifestIntake


def payload() -> dict[str, object]:
    return {
        "schema_version": "crow-health.apple-health-manifest.v1",
        "entries": [
            {
                "identifier": "HKQuantityTypeIdentifierStepCount",
                "source_bundle_id": "com.garmin.connect.mobile",
                "source_name": "Garmin Connect",
                "sample_count": 12,
                "earliest_sample": "2026-08-01T00:00:00Z",
                "latest_sample": "2026-08-06T00:00:00Z",
                "observed_units": ["count"],
            }
        ],
    }


def test_requires_matching_bearer_token(tmp_path: Path) -> None:
    intake = AppleHealthManifestIntake(tmp_path, "secret")

    with pytest.raises(PermissionError):
        intake.authorize("Bearer wrong")

    intake.authorize("Bearer secret")


def test_archives_canonical_payload_idempotently(tmp_path: Path) -> None:
    intake = AppleHealthManifestIntake(tmp_path, "secret")

    first = intake.ingest(payload())
    second = intake.ingest(payload())

    assert first.entry_count == 1
    assert first.existing is False
    assert second.existing is True
    assert first.evidence_id == second.evidence_id
    assert Path(first.path).exists()


def test_rejects_wrong_schema(tmp_path: Path) -> None:
    intake = AppleHealthManifestIntake(tmp_path, "secret")

    with pytest.raises(ValueError, match="Unsupported"):
        intake.ingest({"schema_version": "wrong", "entries": []})
