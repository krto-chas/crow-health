from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from math import fsum

from crow_health.evidence.models import Observation
from crow_health.timeline import ObservationTimeline, TimelineQuery


@dataclass(frozen=True, slots=True)
class StatisticsQuery:
    metric: str
    observed_from: datetime | None = None
    observed_to: datetime | None = None
    source_evidence_id: str | None = None
    parser_name: str | None = None


@dataclass(frozen=True, slots=True)
class DailyStatistics:
    day: date
    count: int
    minimum: float
    maximum: float
    mean: float


@dataclass(frozen=True, slots=True)
class MetricStatistics:
    metric: str
    unit: str | None
    count: int
    minimum: float | None
    maximum: float | None
    mean: float | None
    first_observed_at: datetime | None
    last_observed_at: datetime | None
    covered_days: int
    excluded_non_numeric: int
    excluded_without_timestamp: int
    daily: tuple[DailyStatistics, ...]


class DescriptiveStatistics:
    """Neutral numeric summaries over the read-only observation timeline."""

    def __init__(self, timeline: ObservationTimeline) -> None:
        self._timeline = timeline

    def summarize(self, query: StatisticsQuery) -> MetricStatistics:
        timeline = self._timeline.query(
            TimelineQuery(
                observed_from=query.observed_from,
                observed_to=query.observed_to,
                source_evidence_id=query.source_evidence_id,
                parser_name=query.parser_name,
                metric_prefix=query.metric,
            )
        )
        matching = tuple(
            observation
            for group in timeline.groups
            for observation in group.observations
            if observation.metric == query.metric
        )
        numeric, excluded_non_numeric = _numeric_observations(matching)
        unit = _common_unit(numeric)
        values = [value for _, value in numeric]
        timestamps = [
            observation.observed_at
            for observation, _ in numeric
            if observation.observed_at is not None
        ]
        daily = _daily_statistics(numeric)

        return MetricStatistics(
            metric=query.metric,
            unit=unit,
            count=len(values),
            minimum=min(values) if values else None,
            maximum=max(values) if values else None,
            mean=fsum(values) / len(values) if values else None,
            first_observed_at=min(timestamps) if timestamps else None,
            last_observed_at=max(timestamps) if timestamps else None,
            covered_days=len(daily),
            excluded_non_numeric=excluded_non_numeric,
            excluded_without_timestamp=timeline.excluded_without_timestamp,
            daily=daily,
        )


def _numeric_observations(
    observations: tuple[Observation, ...],
) -> tuple[tuple[tuple[Observation, float], ...], int]:
    numeric: list[tuple[Observation, float]] = []
    excluded = 0
    for observation in observations:
        value = observation.value
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            excluded += 1
            continue
        numeric.append((observation, float(value)))
    return tuple(numeric), excluded


def _common_unit(observations: tuple[tuple[Observation, float], ...]) -> str | None:
    units = {observation.unit for observation, _ in observations}
    if len(units) > 1:
        raise ValueError("Cannot summarize one metric with multiple units")
    return next(iter(units), None)


def _daily_statistics(
    observations: tuple[tuple[Observation, float], ...],
) -> tuple[DailyStatistics, ...]:
    grouped: dict[date, list[float]] = {}
    for observation, value in observations:
        if observation.observed_at is None:
            continue
        grouped.setdefault(observation.observed_at.date(), []).append(value)

    return tuple(
        DailyStatistics(
            day=day,
            count=len(values),
            minimum=min(values),
            maximum=max(values),
            mean=fsum(values) / len(values),
        )
        for day, values in sorted(grouped.items())
    )
