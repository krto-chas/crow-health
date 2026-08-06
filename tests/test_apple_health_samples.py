from __future__ import annotations

from crow_health.apple_health import APPLE_HEALTH_SAMPLE_SCHEMA, load_sample_batch


def _payload() -> dict[str, object]:
    return {
        "schema_version": APPLE_HEALTH_SAMPLE_SCHEMA,
        "collector_id": "iphone-primary",
        "generated_at": "2026-08-06T19:00:00+00:00",
        "anchor": "opaque-anchor",
        "samples": [
            {
                "sample_id": "sample-2",
                "identifier": "HKQuantityTypeIdentifierHeartRate",
                "kind": "quantity",
                "source_bundle_id": "com.garmin.connect.mobile",
                "source_name": "Garmin Connect",
                "start_at": "2026-08-06T18:05:00+00:00",
                "end_at": "2026-08-06T18:05:00+00:00",
                "value": 65,
                "unit": "count/min",
            },
            {
                "sample_id": "sample-1",
                "identifier": "HKCategoryTypeIdentifierSleepAnalysis",
                "kind": "category",
                "source_bundle_id": "com.garmin.connect.mobile",
                "source_name": "Garmin Connect",
                "start_at": "2026-08-05T22:00:00+00:00",
                "end_at": "2026-08-06T06:00:00+00:00",
                "value": "asleepCore",
                "unit": None,
            },
        ],
    }


def test_loads_and_sorts_supported_samples_deterministically() -> None:
    batch = load_sample_batch(_payload())

    assert batch.collector_id == "iphone-primary"
    assert [sample.sample_id for sample in batch.samples] == ["sample-1", "sample-2"]
    assert len(batch.evidence_id) == 64
    assert batch.evidence_id == load_sample_batch(_payload()).evidence_id


def test_rejects_duplicate_sample_ids() -> None:
    payload = _payload()
    samples = payload["samples"]
    assert isinstance(samples, list)
    duplicate = dict(samples[0])
    duplicate["sample_id"] = "sample-1"
    samples.append(duplicate)

    try:
        load_sample_batch(payload)
    except ValueError as exc:
        assert "unique" in str(exc)
    else:
        raise AssertionError("duplicate sample IDs must fail")


def test_rejects_unknown_healthkit_identifier() -> None:
    payload = _payload()
    samples = payload["samples"]
    assert isinstance(samples, list)
    samples[0]["identifier"] = "HKQuantityTypeIdentifierUnknown"

    try:
        load_sample_batch(payload)
    except ValueError as exc:
        assert "Unsupported HealthKit identifier" in str(exc)
    else:
        raise AssertionError("unknown identifier must fail")


def test_requires_units_for_quantity_samples() -> None:
    payload = _payload()
    samples = payload["samples"]
    assert isinstance(samples, list)
    samples[0]["unit"] = None

    try:
        load_sample_batch(payload)
    except ValueError as exc:
        assert "unit is required" in str(exc)
    else:
        raise AssertionError("quantity samples without units must fail")


def test_requires_timezone_aware_timestamps() -> None:
    payload = _payload()
    payload["generated_at"] = "2026-08-06T19:00:00"

    try:
        load_sample_batch(payload)
    except ValueError as exc:
        assert "timezone" in str(exc)
    else:
        raise AssertionError("naive timestamps must fail")
