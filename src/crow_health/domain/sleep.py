from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True, slots=True)
class SleepStages:
    awake_seconds: int
    deep_seconds: int
    light_seconds: int
    rem_seconds: int
    unmeasurable_seconds: int


@dataclass(frozen=True, slots=True)
class SleepRespiration:
    average: float
    highest: float
    lowest: float


@dataclass(frozen=True, slots=True)
class SleepScore:
    overall: int
    quality: int
    recovery: int
    duration: int
    deep: int
    rem: int
    light: int
    restfulness: int
    awake_time: int
    awakenings_count: int
    combined_awake: int
    interruptions: int
    feedback: str
    insight: str


@dataclass(frozen=True, slots=True)
class SleepSession:
    calendar_date: date
    started_at: datetime
    ended_at: datetime
    stages: SleepStages
    respiration: SleepRespiration
    score: SleepScore
    average_stress: float
    awake_count: int
    restless_moment_count: int
    retro: bool
    confirmation_type: str
