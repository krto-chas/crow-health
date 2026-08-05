from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from crow_health.evidence.models import Observation
from crow_health.storage import (
    JsonlObservationIndex,
    JsonlObservationStore,
    ObservationQuery,
)


def _observation(
    observation_id: str,
    *,
    metric: str,
    observed_at: datetime | None,
    source_evidence_id: str = "evidence-1",
    parser_name: str = "garmin-sleep",
) -> Observation:
    return Observation(
        observation_id=observation_id,
        source_evidence_id=source_evidence_id,
        source_path="DI_CONNECT/sample_sleepData.json",
        metric=metric,
        value=42,
        unit=None,
        observed_at=observed_at,
        imported_at=datetime(2026, 8, 5, 18, 0, tzinfo=UTC),
        parser_name=parser_name,
        parser_version="1",
    )


def test_rebuild_and_query_by_metric(tmp_path: Path) -> None:
    store_path = tmp_path / "observations.jsonl"
    store = JsonlObservationStore(store_path)
    first = _observation(
        "one",
        metric="sleep.score.overall",
        observed_at=datetime(2026, 8, 1, tzinfo=UTC),
    )
    second = _observation(
        "two",
        metric="sleep.stage.deep.seconds",
        observed_at=datetime(2026, 8, 2, tzinfo=UTC),
    )
    store.append((first, second))

    index = JsonlObservationIndex(store_path)

    assert index.rebuild() == 2
    assert index.query(ObservationQuery(metric="sleep.score.overall")) == (first,)


def test_query_by_date_source_and_parser(tmp_path: Path) -> None:
    store_path = tmp_path / "observations.jsonl"
    store = JsonlObservationStore(store_path)
    start = datetime(2026, 8, 1, tzinfo=UTC)
    observations = (
        _observation("one", metric="m", observed_at=start),
        _observation(
            "two",
            metric="m",
            observed_at=start + timedelta(days=1),
            source_evidence_id="evidence-2",
            parser_name="other-parser",
        ),
    )
    store.append(observations)
    index = JsonlObservationIndex(store_path)
    index.rebuild()

    assert index.query(
        ObservationQuery(
            source_evidence_id="evidence-2",
            parser_name="other-parser",
            observed_from=start + timedelta(hours=12),
            observed_to=start + timedelta(days=2),
        )
    ) == (observations[1],)


def test_rebuild_is_idempotent_and_replaces_previous_index(tmp_path: Path) -> None:
    store_path = tmp_path / "observations.jsonl"
    store = JsonlObservationStore(store_path)
    store.append(
        (
            _observation(
                "one",
                metric="m",
                observed_at=datetime(2026, 8, 1, tzinfo=UTC),
            ),
        )
    )
    index = JsonlObservationIndex(store_path)

    assert index.rebuild() == 1
    first_content = index.index_path.read_text(encoding="utf-8")
    assert index.rebuild() == 1
    assert index.index_path.read_text(encoding="utf-8") == first_content


def test_empty_store_builds_empty_index(tmp_path: Path) -> None:
    index = JsonlObservationIndex(tmp_path / "missing.jsonl")

    assert index.rebuild() == 0
    assert index.entries() == ()
    assert index.query(ObservationQuery()) == ()


def test_corrupt_store_does_not_replace_existing_index(tmp_path: Path) -> None:
    store_path = tmp_path / "observations.jsonl"
    index_path = tmp_path / "observations.index"
    index_path.write_text('{"sentinel": true}\n', encoding="utf-8")
    store_path.write_text("not-json\n", encoding="utf-8")
    index = JsonlObservationIndex(store_path, index_path)

    with pytest.raises(json.JSONDecodeError):
        index.rebuild()

    assert index_path.read_text(encoding="utf-8") == '{"sentinel": true}\n'


def test_query_detects_stale_index_offsets(tmp_path: Path) -> None:
    store_path = tmp_path / "observations.jsonl"
    store = JsonlObservationStore(store_path)
    store.append(
        (
            _observation(
                "one",
                metric="m",
                observed_at=datetime(2026, 8, 1, tzinfo=UTC),
            ),
        )
    )
    index = JsonlObservationIndex(store_path)
    index.rebuild()
    changed = store_path.read_text(encoding="utf-8").replace('"one"', '"two"')
    store_path.write_text(changed, encoding="utf-8")

    with pytest.raises(ValueError, match="does not match"):
        index.query(ObservationQuery())
