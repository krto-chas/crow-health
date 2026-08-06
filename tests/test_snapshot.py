from datetime import UTC, datetime
from pathlib import Path

import pytest

from crow_health.analytics import AnalyticsService
from crow_health.evidence.models import Observation
from crow_health.snapshot import SNAPSHOT_SCHEMA_VERSION, SnapshotQuery, SnapshotService
from crow_health.statistics import DescriptiveStatistics
from crow_health.storage import JsonlObservationIndex, JsonlObservationStore
from crow_health.timeline import ObservationTimeline


def observation(
    observation_id: str,
    metric: str,
    value: float,
    observed_at: datetime,
    *,
    unit: str | None = None,
) -> Observation:
    return Observation(
        observation_id=observation_id,
        source_evidence_id="evidence-1",
        source_path="sample.json",
        metric=metric,
        value=value,
        unit=unit,
        observed_at=observed_at,
        imported_at=datetime(2026, 8, 6, tzinfo=UTC),
        parser_name="garmin-sleep",
        parser_version="2",
    )


def service(tmp_path: Path, items: tuple[Observation, ...]) -> SnapshotService:
    store_path = tmp_path / "observations.jsonl"
    JsonlObservationStore(store_path).append(items)
    index = JsonlObservationIndex(store_path)
    index.rebuild()
    statistics = DescriptiveStatistics(ObservationTimeline(index))
    return SnapshotService(statistics, AnalyticsService(statistics))


def test_builds_compact_snapshot_in_metric_order(tmp_path: Path) -> None:
    snapshot = service(
        tmp_path,
        (
            observation("a", "sleep.score.overall", 80, datetime(2026, 8, 1, tzinfo=UTC), unit="score"),
            observation("b", "sleep.score.overall", 90, datetime(2026, 8, 2, tzinfo=UTC), unit="score"),
            observation("c", "sleep.average_stress", 20, datetime(2026, 8, 1, tzinfo=UTC)),
        ),
    ).build(
        SnapshotQuery(
            metrics=("sleep.score.overall", "sleep.average_stress"),
            moving_average_window_days=2,
        )
    )

    assert snapshot.schema_version == SNAPSHOT_SCHEMA_VERSION
    assert [item.metric for item in snapshot.metrics] == [
        "sleep.average_stress",
        "sleep.score.overall",
    ]
    score = snapshot.metrics[1]
    assert score.observation_count == 2
    assert score.latest_value == 90
    assert score.moving_average == 85
    assert score.trend_direction == "up"
    assert score.trend_difference == 10
    assert score.coverage_percent == 100


def test_empty_metric_is_explicit_not_invented(tmp_path: Path) -> None:
    snapshot = service(tmp_path, ()).build(SnapshotQuery(metrics=("missing",)))

    metric = snapshot.metrics[0]
    assert metric.observation_count == 0
    assert metric.latest_value is None
    assert metric.moving_average is None
    assert metric.trend_direction is None
    assert metric.coverage_percent is None


def test_deduplicates_metrics_deterministically(tmp_path: Path) -> None:
    snapshot = service(tmp_path, ()).build(
        SnapshotQuery(metrics=("b", "a", "b"))
    )

    assert [item.metric for item in snapshot.metrics] == ["a", "b"]


def test_requires_at_least_one_metric(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="At least one metric"):
        service(tmp_path, ()).build(SnapshotQuery(metrics=()))


def test_rejects_invalid_window(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="at least 1"):
        service(tmp_path, ()).build(
            SnapshotQuery(metrics=("metric",), moving_average_window_days=0)
        )
