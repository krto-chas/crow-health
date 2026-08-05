from __future__ import annotations

from datetime import date, timedelta
from math import fsum
from statistics import quantiles

from crow_health.analytics.models import (
    AnalyticsQuery,
    CompletenessResult,
    MovingAveragePoint,
    MovingAverageResult,
    OutlierPoint,
    OutlierResult,
    TrendDirection,
    TrendResult,
)
from crow_health.statistics import DescriptiveStatistics, StatisticsQuery


class AnalyticsService:
    """Deterministic, non-medical analytics over daily metric summaries."""

    def __init__(self, statistics: DescriptiveStatistics) -> None:
        self._statistics = statistics

    def moving_average(
        self, query: AnalyticsQuery, *, window_days: int = 7
    ) -> MovingAverageResult:
        if window_days < 1:
            raise ValueError("window_days must be at least 1")
        summary = self._summary(query)
        daily = summary.daily
        points: list[MovingAveragePoint] = []
        for current in daily:
            start = current.day - timedelta(days=window_days - 1)
            values = [item.mean for item in daily if start <= item.day <= current.day]
            points.append(
                MovingAveragePoint(
                    day=current.day,
                    value=fsum(values) / len(values),
                    window_observations=len(values),
                )
            )
        return MovingAverageResult(
            metric=query.metric,
            unit=summary.unit,
            window_days=window_days,
            points=tuple(points),
        )

    def trend(self, query: AnalyticsQuery) -> TrendResult:
        summary = self._summary(query)
        if not summary.daily:
            return TrendResult(
                metric=query.metric,
                unit=summary.unit,
                first_day=None,
                last_day=None,
                first_value=None,
                last_value=None,
                difference=None,
                percent_change=None,
                direction=None,
            )
        first = summary.daily[0]
        last = summary.daily[-1]
        difference = last.mean - first.mean
        percent_change = None if first.mean == 0 else difference / first.mean * 100
        direction = TrendDirection.UNCHANGED
        if difference > 0:
            direction = TrendDirection.UP
        elif difference < 0:
            direction = TrendDirection.DOWN
        return TrendResult(
            metric=query.metric,
            unit=summary.unit,
            first_day=first.day,
            last_day=last.day,
            first_value=first.mean,
            last_value=last.mean,
            difference=difference,
            percent_change=percent_change,
            direction=direction,
        )

    def completeness(self, query: AnalyticsQuery) -> CompletenessResult:
        summary = self._summary(query)
        start = query.observed_from.date() if query.observed_from else None
        end = query.observed_to.date() if query.observed_to else None
        if start is None and summary.first_observed_at is not None:
            start = summary.first_observed_at.date()
        if end is None and summary.last_observed_at is not None:
            end = summary.last_observed_at.date()
        if start is None or end is None:
            return CompletenessResult(query.metric, start, end, 0, 0, 0, None)
        if end < start:
            raise ValueError("observed_to must not be before observed_from")
        expected = (end - start).days + 1
        observed = len({item.day for item in summary.daily if start <= item.day <= end})
        return CompletenessResult(
            metric=query.metric,
            range_start=start,
            range_end=end,
            expected_days=expected,
            observed_days=observed,
            missing_days=expected - observed,
            coverage_percent=observed / expected * 100,
        )

    def outliers(self, query: AnalyticsQuery) -> OutlierResult:
        summary = self._summary(query)
        daily = summary.daily
        if len(daily) < 4:
            return OutlierResult(query.metric, summary.unit, "iqr", None, None, ())
        quartiles = quantiles([item.mean for item in daily], n=4, method="inclusive")
        lower_quartile, upper_quartile = quartiles[0], quartiles[2]
        iqr = upper_quartile - lower_quartile
        lower_bound = lower_quartile - 1.5 * iqr
        upper_bound = upper_quartile + 1.5 * iqr
        points = tuple(
            OutlierPoint(day=item.day, value=item.mean)
            for item in daily
            if item.mean < lower_bound or item.mean > upper_bound
        )
        return OutlierResult(
            metric=query.metric,
            unit=summary.unit,
            method="iqr",
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            points=points,
        )

    def _summary(self, query: AnalyticsQuery):
        return self._statistics.summarize(
            StatisticsQuery(
                metric=query.metric,
                observed_from=query.observed_from,
                observed_to=query.observed_to,
                source_evidence_id=query.source_evidence_id,
                parser_name=query.parser_name,
            )
        )
