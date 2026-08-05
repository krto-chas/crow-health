from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from crow_health.evidence.models import Observation
from crow_health.storage import JsonlObservationStore
from crow_health.validation import validate_store


def _observation(observation_id: str, metric: str, when: datetime | None) -> Observation:
    return Observation(
        observation_id=observation_id,
        source_evidence_id="source-1",
        source_path="sample.json",
        metric=metric,
        value=1,
        unit=None,
        observed_at=when,
        imported_at=datetime(2026, 8, 5, tzinfo=UTC),
        parser_name="test-parser",
        parser_version="1",
    )


def test_validate_store_rebuilds_index_and_summarizes_data(tmp_path: Path) -> None:
    store_path = tmp_path / "observations.jsonl"
    store = JsonlObservationStore(store_path)
    first = datetime(2026, 8, 1, tzinfo=UTC)
    second = datetime(2026, 8, 2, tzinfo=UTC)
    store.append(
        (
            _observation("one", "sleep.score.overall", first),
            _observation("two", "sleep.score.overall", second),
            _observation("three", "sleep.stage.deep.seconds", None),
        )
    )

    report = validate_store(store_path)

    assert report.succeeded
    assert report.observation_count == 3
    assert report.index_entry_count == 3
    assert report.metric_counts == {
        "sleep.score.overall": 2,
        "sleep.stage.deep.seconds": 1,
    }
    assert report.parser_counts == {"test-parser": 3}
    assert report.source_count == 1
    assert report.observations_without_timestamp == 1
    assert report.observed_from == first
    assert report.observed_to == second


def test_validate_empty_store(tmp_path: Path) -> None:
    report = validate_store(tmp_path / "missing.jsonl")

    assert report.succeeded
    assert report.observation_count == 0
    assert report.index_entry_count == 0
    assert report.observed_from is None
    assert report.observed_to is None
