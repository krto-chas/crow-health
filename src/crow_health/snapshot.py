from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime
from typing import Any

from crow_health.analytics import AnalyticsQuery, AnalyticsService
from crow_health.statistics import DescriptiveStatistics, StatisticsQuery


SNAPSHOT_SCHEMA_VERSION = "crow-health.snapshot.v1"


@dataclass(frozen=True, slots=True)
class SnapshotQuery:
    metrics: tuple[str, ...]
    observed_from: datetime | None = None
    observed_to: datetime | None = None
    source_evidence_id: str | None = None
    parser_name: str | None = None
    moving_average_window_days: int = 7


@dataclass(frozen=True, slots=True)
class SnapshotMetric:
    metric: str
    unit: str | None
    observation_count: int
    covered_days: int
    first_observed_at: datetime | None
    last_observed_at: datetime | None
    minimum: float | None
    maximum: float | None
    mean: float | None
    latest_day: date | None
    latest_value: float | None
    moving_average: float | None
    trend_direction: str | None
    trend_difference: float | None
    trend_percent_change: float | None
    coverage_percent: float | None
    expected_days: int
    observed_days: int
    missing_days: int
    outlier_count: int


@dataclass(frozen=True, slots=True)
class PresentationSnapshot:
    schema_version: str
    observed_from: datetime | None
    observed_to: datetime | None
    source_evidence_id: str | None
    parser_name: str | None
    moving_average_window_days: int
    metrics: tuple[SnapshotMetric, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SnapshotService:
    """Build a compact, deterministic read model for external presentation layers."""

    def __init__(
        self,
        statistics: DescriptiveStatistics,
        analytics: AnalyticsService,
    ) -> None:
        self._statistics = statistics
        self._analytics = analytics

    def build(self, query: SnapshotQuery) -> PresentationSnapshot:
        metrics = tuple(sorted(set(query.metrics)))
        if not metrics:
            raise ValueError("At least one metric is required")
        if query.moving_average_window_days < 1:
            raise ValueError("moving_average_window_days must be at least 1")

        entries = tuple(self._metric(metric, query) for metric in metrics)
        return PresentationSnapshot(
            schema_version=SNAPSHOT_SCHEMA_VERSION,
            observed_from=query.observed_from,
            observed_to=query.observed_to,
            source_evidence_id=query.source_evidence_id,
            parser_name=query.parser_name,
            moving_average_window_days=query.moving_average_window_days,
            metrics=entries,
        )

    def _metric(self, metric: str, query: SnapshotQuery) -> SnapshotMetric:
        statistics_query = StatisticsQuery(
            metric=metric,
            observed_from=query.observed_from,
            observed_to=query.observed_to,
            source_evidence_id=query.source_evidence_id,
            parser_name=query.parser_name,
        )
        analytics_query = AnalyticsQuery(
            metric=metric,
            observed_from=query.observed_from,
            observed_to=query.observed_to,
            source_evidence_id=query.source_evidence_id,
            parser_name=query.parser_name,
        )
        summary = self._statistics.summarize(statistics_query)
        moving_average = self._analytics.moving_average(
            analytics_query,
            window_days=query.moving_average_window_days,
        )
        trend = self._analytics.trend(analytics_query)
        completeness = self._analytics.completeness(analytics_query)
        outliers = self._analytics.outliers(analytics_query)
        latest = summary.daily[-1] if summary.daily else None
        latest_average = moving_average.points[-1] if moving_average.points else None

        return SnapshotMetric(
            metric=metric,
            unit=summary.unit,
            observation_count=summary.count,
            covered_days=summary.covered_days,
            first_observed_at=summary.first_observed_at,
            last_observed_at=summary.last_observed_at,
            minimum=summary.minimum,
            maximum=summary.maximum,
            mean=summary.mean,
            latest_day=latest.day if latest is not None else None,
            latest_value=latest.mean if latest is not None else None,
            moving_average=(
                latest_average.value if latest_average is not None else None
            ),
            trend_direction=(
                trend.direction.value if trend.direction is not None else None
            ),
            trend_difference=trend.difference,
            trend_percent_change=trend.percent_change,
            coverage_percent=completeness.coverage_percent,
            expected_days=completeness.expected_days,
            observed_days=completeness.observed_days,
            missing_days=completeness.missing_days,
            outlier_count=len(outliers.points),
        )
