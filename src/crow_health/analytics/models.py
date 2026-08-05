from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum


class TrendDirection(StrEnum):
    UP = "up"
    DOWN = "down"
    UNCHANGED = "unchanged"


@dataclass(frozen=True, slots=True)
class AnalyticsQuery:
    metric: str
    observed_from: datetime | None = None
    observed_to: datetime | None = None
    source_evidence_id: str | None = None
    parser_name: str | None = None


@dataclass(frozen=True, slots=True)
class MovingAveragePoint:
    day: date
    value: float
    window_observations: int


@dataclass(frozen=True, slots=True)
class MovingAverageResult:
    metric: str
    unit: str | None
    window_days: int
    points: tuple[MovingAveragePoint, ...]


@dataclass(frozen=True, slots=True)
class TrendResult:
    metric: str
    unit: str | None
    first_day: date | None
    last_day: date | None
    first_value: float | None
    last_value: float | None
    difference: float | None
    percent_change: float | None
    direction: TrendDirection | None


@dataclass(frozen=True, slots=True)
class CompletenessResult:
    metric: str
    range_start: date | None
    range_end: date | None
    expected_days: int
    observed_days: int
    missing_days: int
    coverage_percent: float | None


@dataclass(frozen=True, slots=True)
class OutlierPoint:
    day: date
    value: float


@dataclass(frozen=True, slots=True)
class OutlierResult:
    metric: str
    unit: str | None
    method: str
    lower_bound: float | None
    upper_bound: float | None
    points: tuple[OutlierPoint, ...]
