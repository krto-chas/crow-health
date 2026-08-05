from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True, slots=True)
class SleepStages:
    awake_seconds: int | None
    deep_seconds: int | None
    light_seconds: int | None
    rem_seconds: int | None
    unmeasurable_seconds: int | None


@dataclass(frozen=True, slots=True)
class SleepRespiration:
    average: float | None
    highest: float | None
    lowest: float | None


@dataclass(frozen=True, slots=True)
class SleepScore:
    overall: int | None
    quality: int | None
    recovery: int | None
    duration: int | None
    deep: int | None
    rem: int | None
    light: int | None
    restfulness: int | None
    awake_time: int | None
    awakenings_count: int | None
    combined_awake: int | None
    interruptions: int | None
    feedback: str | None
    insight: str | None


@dataclass(frozen=True, slots=True)
class SleepSession:
    calendar_date: date
    started_at: datetime
    ended_at: datetime
    stages: SleepStages
    respiration: SleepRespiration
    score: SleepScore | None
    average_stress: float | None
    awake_count: int | None
    restless_moment_count: int | None
    retro: bool | None
    confirmation_type: str | None
