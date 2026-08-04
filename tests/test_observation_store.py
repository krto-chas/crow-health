from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from crow_health.evidence.models import Observation
from crow_health.storage import JsonlObservationStore, ObservationConflictError


def observation(*, observation_id: str = "obs-1", value: int = 42) -> Observation:
    return Observation(
        observation_id=observation_id,
        source_evidence_id="evidence-1",
        source_path="sleepData.json",
        metric="sleep.score.overall",
        value=value,
        unit="score",
        observed_at=datetime(2026, 8, 4, 1, 0, tzinfo=UTC),
        imported_at=datetime(2026, 8, 4, 8, 0, tzinfo=UTC),
        parser_name="garmin-sleep",
        parser_version="1",
    )


def test_append_and_read_round_trip(tmp_path: Path) -> None:
    store = JsonlObservationStore(tmp_path / "observations.jsonl")

    result = store.append((observation(),))

    assert result.inserted == 1
    assert result.existing == 0
    assert store.all() == (observation(),)
    assert store.get("obs-1") == observation()


def test_repeated_identical_append_is_idempotent(tmp_path: Path) -> None:
    store = JsonlObservationStore(tmp_path / "observations.jsonl")
    store.append((observation(),))

    result = store.append((observation(),))

    assert result.inserted == 0
    assert result.existing == 1
    assert len(store.all()) == 1


def test_conflicting_content_for_same_id_is_rejected(tmp_path: Path) -> None:
    store = JsonlObservationStore(tmp_path / "observations.jsonl")
    store.append((observation(),))

    with pytest.raises(ObservationConflictError, match="conflicting content"):
        store.append((observation(value=43),))


def test_append_is_atomic_before_file_write_on_conflict(tmp_path: Path) -> None:
    store = JsonlObservationStore(tmp_path / "observations.jsonl")
    store.append((observation(),))

    with pytest.raises(ObservationConflictError):
        store.append(
            (
                observation(observation_id="obs-2"),
                observation(value=99),
            )
        )

    assert store.get("obs-2") is None
    assert store.all() == (observation(),)


def test_duplicate_ids_in_existing_file_are_rejected(tmp_path: Path) -> None:
    path = tmp_path / "observations.jsonl"
    store = JsonlObservationStore(path)
    store.append((observation(),))
    first_line = path.read_text(encoding="utf-8")
    path.write_text(first_line + first_line, encoding="utf-8")

    with pytest.raises(ObservationConflictError, match="Duplicate observation ID"):
        store.all()


def test_unsupported_stored_value_type_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "observations.jsonl"
    payload = {
        "observation_id": "obs-1",
        "source_evidence_id": "evidence-1",
        "source_path": "sleepData.json",
        "metric": "sleep.invalid",
        "value": [1, 2],
        "unit": None,
        "observed_at": None,
        "imported_at": "2026-08-04T08:00:00+00:00",
        "parser_name": "garmin-sleep",
        "parser_version": "1",
    }
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")

    with pytest.raises(TypeError, match="unsupported type"):
        JsonlObservationStore(path).all()
