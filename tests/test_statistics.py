from datetime import UTC, datetime
from pathlib import Path

import pytest

from crow_health.evidence.models import Observation
from crow_health.statistics import DescriptiveStatistics, StatisticsQuery
from crow_health.storage import JsonlObservationIndex, JsonlObservationStore
from crow_health.timeline import ObservationTimeline


def observation(
    observation_id: str,
    metric: str,
    value: float | str | bool | None,
    observed_at: datetime | None,
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
        imported_at=datetime(2026, 8, 5, tzinfo=UTC),
        parser_name="garmin-sleep",
        parser_version="2",
    )


def statistics(tmp_path: Path, items: tuple[Observation, ...]) -> DescriptiveStatistics:
    store_path = tmp_path / "observations.jsonl"
    JsonlObservationStore(store_path).append(items)
    index = JsonlObservationIndex(store_path)
    index.rebuild()
    return DescriptiveStatistics(ObservationTimeline(index))


def test_summarizes_numeric_metric_and_daily_values(tmp_path: Path) -> None:
    result = statistics(
        tmp_path,
        (
            observation("a", "sleep.average_stress", 10, datetime(2026, 8, 1, tzinfo=UTC)),
            observation("b", "sleep.average_stress", 20, datetime(2026, 8, 1, 1, tzinfo=UTC)),
            observation("c", "sleep.average_stress", 30, datetime(2026, 8, 2, tzinfo=UTC)),
        ),
    ).summarize(StatisticsQuery(metric="sleep.average_stress"))

    assert result.count == 3
    assert result.minimum == 10
    assert result.maximum == 30
    assert result.mean == 20
    assert result.covered_days == 2
    assert [item.count for item in result.daily] == [2, 1]
    assert result.daily[0].mean == 15


def test_excludes_non_numeric_values_without_coercion(tmp_path: Path) -> None:
    result = statistics(
        tmp_path,
        (
            observation("number", "metric", 12.5, datetime(2026, 8, 1, tzinfo=UTC)),
            observation("text", "metric", "12.5", datetime(2026, 8, 2, tzinfo=UTC)),
            observation("boolean", "metric", True, datetime(2026, 8, 3, tzinfo=UTC)),
        ),
    ).summarize(StatisticsQuery(metric="metric"))

    assert result.count == 1
    assert result.mean == 12.5
    assert result.excluded_non_numeric == 2


def test_empty_metric_returns_explicit_empty_summary(tmp_path: Path) -> None:
    result = statistics(tmp_path, ()).summarize(StatisticsQuery(metric="missing"))

    assert result.count == 0
    assert result.minimum is None
    assert result.maximum is None
    assert result.mean is None
    assert result.daily == ()


def test_rejects_mixed_units_for_one_metric(tmp_path: Path) -> None:
    view = statistics(
        tmp_path,
        (
            observation("a", "metric", 1, datetime(2026, 8, 1, tzinfo=UTC), unit="s"),
            observation("b", "metric", 2, datetime(2026, 8, 2, tzinfo=UTC), unit="ms"),
        ),
    )

    with pytest.raises(ValueError, match="multiple units"):
        view.summarize(StatisticsQuery(metric="metric"))


def test_applies_explicit_time_range(tmp_path: Path) -> None:
    result = statistics(
        tmp_path,
        (
            observation("before", "metric", 1, datetime(2026, 7, 31, tzinfo=UTC)),
            observation("inside", "metric", 2, datetime(2026, 8, 1, tzinfo=UTC)),
        ),
    ).summarize(
        StatisticsQuery(
            metric="metric",
            observed_from=datetime(2026, 8, 1, tzinfo=UTC),
        )
    )

    assert result.count == 1
    assert result.mean == 2
