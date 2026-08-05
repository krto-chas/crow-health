from datetime import UTC, datetime
from pathlib import Path

import pytest

from crow_health.analytics import AnalyticsQuery, AnalyticsService, TrendDirection
from crow_health.evidence.models import Observation
from crow_health.statistics import DescriptiveStatistics
from crow_health.storage import JsonlObservationIndex, JsonlObservationStore
from crow_health.timeline import ObservationTimeline


def observation(
    observation_id: str,
    value: float,
    observed_at: datetime,
) -> Observation:
    return Observation(
        observation_id=observation_id,
        source_evidence_id="evidence-1",
        source_path="sample.json",
        metric="sleep.average_stress",
        value=value,
        unit="score",
        observed_at=observed_at,
        imported_at=datetime(2026, 8, 5, tzinfo=UTC),
        parser_name="garmin-sleep",
        parser_version="2",
    )


def service(tmp_path: Path, items: tuple[Observation, ...]) -> AnalyticsService:
    store_path = tmp_path / "observations.jsonl"
    JsonlObservationStore(store_path).append(items)
    index = JsonlObservationIndex(store_path)
    index.rebuild()
    return AnalyticsService(DescriptiveStatistics(ObservationTimeline(index)))


def query() -> AnalyticsQuery:
    return AnalyticsQuery(metric="sleep.average_stress")


def test_moving_average_uses_calendar_window(tmp_path: Path) -> None:
    result = service(
        tmp_path,
        (
            observation("a", 10, datetime(2026, 8, 1, tzinfo=UTC)),
            observation("b", 20, datetime(2026, 8, 2, tzinfo=UTC)),
            observation("c", 40, datetime(2026, 8, 4, tzinfo=UTC)),
        ),
    ).moving_average(query(), window_days=2)

    assert [point.value for point in result.points] == [10, 15, 40]
    assert [point.window_observations for point in result.points] == [1, 2, 1]


def test_rejects_invalid_moving_average_window(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="window_days"):
        service(tmp_path, ()).moving_average(query(), window_days=0)


def test_trend_reports_first_to_last_change(tmp_path: Path) -> None:
    result = service(
        tmp_path,
        (
            observation("a", 20, datetime(2026, 8, 1, tzinfo=UTC)),
            observation("b", 30, datetime(2026, 8, 2, tzinfo=UTC)),
        ),
    ).trend(query())

    assert result.difference == 10
    assert result.percent_change == 50
    assert result.direction is TrendDirection.UP


def test_empty_trend_is_explicit(tmp_path: Path) -> None:
    result = service(tmp_path, ()).trend(query())

    assert result.direction is None
    assert result.difference is None


def test_completeness_counts_missing_calendar_days(tmp_path: Path) -> None:
    result = service(
        tmp_path,
        (
            observation("a", 10, datetime(2026, 8, 1, tzinfo=UTC)),
            observation("b", 20, datetime(2026, 8, 3, tzinfo=UTC)),
        ),
    ).completeness(query())

    assert result.expected_days == 3
    assert result.observed_days == 2
    assert result.missing_days == 1
    assert result.coverage_percent == pytest.approx(66.6666666667)


def test_iqr_flags_statistical_outlier(tmp_path: Path) -> None:
    values = (10, 10, 11, 9, 10, 100)
    items = tuple(
        observation(str(index), value, datetime(2026, 8, index, tzinfo=UTC))
        for index, value in enumerate(values, start=1)
    )

    result = service(tmp_path, items).outliers(query())

    assert result.method == "iqr"
    assert [(point.day.day, point.value) for point in result.points] == [(6, 100)]


def test_outliers_require_four_daily_values(tmp_path: Path) -> None:
    result = service(
        tmp_path,
        (observation("a", 10, datetime(2026, 8, 1, tzinfo=UTC)),),
    ).outliers(query())

    assert result.lower_bound is None
    assert result.points == ()
