from datetime import UTC, datetime

from crow_health.parsers.defaults import default_parser_registry
from crow_health.parsers.garmin_sleep import GarminSleepParser
from crow_health.parsers.models import SourceDocument


def sleep_record() -> dict[str, object]:
    return {
        "averageRespiration": 14.2,
        "avgSleepStress": 18.0,
        "awakeCount": 3,
        "awakeSleepSeconds": 900,
        "calendarDate": "2026-08-01",
        "deepSleepSeconds": 5400,
        "highestRespiration": 18.1,
        "lightSleepSeconds": 12600,
        "lowestRespiration": 10.4,
        "remSleepSeconds": 6300,
        "restlessMomentCount": 12,
        "retro": False,
        "sleepEndTimestampGMT": "2026-08-01T05:30:00Z",
        "sleepScores": {
            "awakeTimeScore": 80,
            "awakeningsCountScore": 81,
            "combinedAwakeScore": 82,
            "deepScore": 83,
            "durationScore": 84,
            "feedback": "synthetic fixture",
            "insight": "synthetic fixture",
            "interruptionsScore": 85,
            "lightScore": 86,
            "overallScore": 87,
            "qualityScore": 88,
            "recoveryScore": 89,
            "remScore": 90,
            "restfulnessScore": 91,
        },
        "sleepStartTimestampGMT": "2026-07-31T21:30:00Z",
        "sleepWindowConfirmationType": "SYNTHETIC",
        "unmeasurableSeconds": 0,
    }


def document(payload: object) -> SourceDocument:
    assert isinstance(payload, (dict, list))
    return SourceDocument(
        evidence_id="evidence-1",
        source_path="DI_CONNECT/DI-Connect-Wellness/sample_sleepData.json",
        media_type="application/json",
        checksum="abc",
        payload=payload,
    )


def test_parser_normalizes_observed_sleep_schema() -> None:
    imported_at = datetime(2026, 8, 4, tzinfo=UTC)
    result = GarminSleepParser(imported_at=imported_at).parse(document([sleep_record()]))

    assert result.errors == ()
    assert len(result.records) == 27
    metrics = {record.metric: record for record in result.records}
    assert metrics["sleep.deep_seconds"].value == 5400
    assert metrics["sleep.score.overall"].value == 87
    assert metrics["sleep.respiration.average"].value == 14.2
    assert all(record.source_evidence_id == "evidence-1" for record in result.records)
    assert all(record.imported_at == imported_at for record in result.records)


def test_legacy_record_without_score_object_preserves_available_measurements() -> None:
    raw = sleep_record()
    raw["sleepScores"] = None

    result = GarminSleepParser().parse(document([raw]))

    metrics = {record.metric for record in result.records}
    assert result.errors == ()
    assert "sleep.deep_seconds" in metrics
    assert "sleep.score.overall" not in metrics
    assert result.warnings[0].code == "legacy_sleep_scores_unavailable"


def test_missing_optional_modern_fields_are_omitted() -> None:
    raw = sleep_record()
    del raw["remSleepSeconds"]
    scores = raw["sleepScores"]
    assert isinstance(scores, dict)
    del scores["interruptionsScore"]

    result = GarminSleepParser().parse(document([raw]))

    metrics = {record.metric for record in result.records}
    assert result.errors == ()
    assert "sleep.rem_seconds" not in metrics
    assert "sleep.score.interruptions" not in metrics
    assert "sleep.score.overall" in metrics


def test_observation_ids_are_deterministic() -> None:
    parser = GarminSleepParser(imported_at=datetime(2026, 8, 4, tzinfo=UTC))
    first = parser.parse(document([sleep_record()]))
    second = parser.parse(document([sleep_record()]))

    assert [item.observation_id for item in first.records] == [
        item.observation_id for item in second.records
    ]


def test_invalid_record_is_reported_without_guessing() -> None:
    raw = sleep_record()
    del raw["calendarDate"]

    result = GarminSleepParser().parse(document([raw]))

    assert result.records == ()
    assert len(result.errors) == 1
    assert result.errors[0].code == "invalid_sleep_record"
    assert "calendarDate" in result.errors[0].message


def test_root_must_be_array() -> None:
    result = GarminSleepParser().parse(document({"not": "an array"}))

    assert result.records == ()
    assert result.errors[0].code == "root_type"


def test_default_registry_matches_sleep_documents() -> None:
    registry = default_parser_registry()
    source = document([sleep_record()])

    matches = registry.matching(source)

    assert len(matches) == 1
    assert matches[0].parser.name == "garmin-sleep"
