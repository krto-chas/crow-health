from __future__ import annotations

from datetime import UTC, date, datetime
from hashlib import sha256
from typing import Any, Callable

from crow_health.domain.sleep import (
    SleepRespiration,
    SleepScore,
    SleepSession,
    SleepStages,
)
from crow_health.evidence.models import Observation
from crow_health.parsers.models import ParseMessage, ParseResult, SourceDocument


class GarminSleepParser:
    name = "garmin-sleep"
    version = "1"
    supported_path_patterns = ("*sleepData.json",)
    supported_media_types = ("application/json",)

    def __init__(self, *, imported_at: datetime | None = None) -> None:
        self._imported_at = imported_at or datetime.now(UTC)

    def parse(self, document: SourceDocument) -> ParseResult:
        if not isinstance(document.payload, list):
            return self._failure(document, "root_type", "Expected a JSON array")

        observations: list[Observation] = []
        errors: list[ParseMessage] = []
        for index, raw in enumerate(document.payload):
            try:
                session = self.parse_session(raw)
            except (KeyError, TypeError, ValueError) as exc:
                errors.append(
                    ParseMessage(
                        code="invalid_sleep_record",
                        message=f"Record {index}: {exc}",
                    )
                )
                continue
            observations.extend(self._observations(document, session))

        return ParseResult(
            records=tuple(observations),
            warnings=(),
            errors=tuple(errors),
            parser_name=self.name,
            parser_version=self.version,
            source_evidence_id=document.evidence_id,
        )

    def parse_session(self, raw: object) -> SleepSession:
        record = _object(raw, "record")
        scores = _object(record.get("sleepScores"), "sleepScores")
        return SleepSession(
            calendar_date=_date(record, "calendarDate"),
            started_at=_timestamp(record, "sleepStartTimestampGMT"),
            ended_at=_timestamp(record, "sleepEndTimestampGMT"),
            stages=SleepStages(
                awake_seconds=_integer(record, "awakeSleepSeconds"),
                deep_seconds=_integer(record, "deepSleepSeconds"),
                light_seconds=_integer(record, "lightSleepSeconds"),
                rem_seconds=_integer(record, "remSleepSeconds"),
                unmeasurable_seconds=_integer(record, "unmeasurableSeconds"),
            ),
            respiration=SleepRespiration(
                average=_number(record, "averageRespiration"),
                highest=_number(record, "highestRespiration"),
                lowest=_number(record, "lowestRespiration"),
            ),
            score=SleepScore(
                overall=_integer(scores, "overallScore"),
                quality=_integer(scores, "qualityScore"),
                recovery=_integer(scores, "recoveryScore"),
                duration=_integer(scores, "durationScore"),
                deep=_integer(scores, "deepScore"),
                rem=_integer(scores, "remScore"),
                light=_integer(scores, "lightScore"),
                restfulness=_integer(scores, "restfulnessScore"),
                awake_time=_integer(scores, "awakeTimeScore"),
                awakenings_count=_integer(scores, "awakeningsCountScore"),
                combined_awake=_integer(scores, "combinedAwakeScore"),
                interruptions=_integer(scores, "interruptionsScore"),
                feedback=_string(scores, "feedback"),
                insight=_string(scores, "insight"),
            ),
            average_stress=_number(record, "avgSleepStress"),
            awake_count=_integer(record, "awakeCount"),
            restless_moment_count=_integer(record, "restlessMomentCount"),
            retro=_boolean(record, "retro"),
            confirmation_type=_string(record, "sleepWindowConfirmationType"),
        )

    def _observations(
        self,
        document: SourceDocument,
        session: SleepSession,
    ) -> list[Observation]:
        values: tuple[tuple[str, int | float | str | bool, str | None], ...] = (
            ("sleep.awake_seconds", session.stages.awake_seconds, "s"),
            ("sleep.deep_seconds", session.stages.deep_seconds, "s"),
            ("sleep.light_seconds", session.stages.light_seconds, "s"),
            ("sleep.rem_seconds", session.stages.rem_seconds, "s"),
            ("sleep.unmeasurable_seconds", session.stages.unmeasurable_seconds, "s"),
            ("sleep.awake_count", session.awake_count, "count"),
            ("sleep.restless_moment_count", session.restless_moment_count, "count"),
            ("sleep.average_stress", session.average_stress, None),
            ("sleep.respiration.average", session.respiration.average, None),
            ("sleep.respiration.highest", session.respiration.highest, None),
            ("sleep.respiration.lowest", session.respiration.lowest, None),
            ("sleep.score.overall", session.score.overall, "score"),
            ("sleep.score.quality", session.score.quality, "score"),
            ("sleep.score.recovery", session.score.recovery, "score"),
            ("sleep.score.duration", session.score.duration, "score"),
            ("sleep.score.deep", session.score.deep, "score"),
            ("sleep.score.rem", session.score.rem, "score"),
            ("sleep.score.light", session.score.light, "score"),
            ("sleep.score.restfulness", session.score.restfulness, "score"),
            ("sleep.score.awake_time", session.score.awake_time, "score"),
            ("sleep.score.awakenings_count", session.score.awakenings_count, "score"),
            ("sleep.score.combined_awake", session.score.combined_awake, "score"),
            ("sleep.score.interruptions", session.score.interruptions, "score"),
            ("sleep.score.feedback", session.score.feedback, None),
            ("sleep.score.insight", session.score.insight, None),
            ("sleep.retro", session.retro, None),
            ("sleep.confirmation_type", session.confirmation_type, None),
        )
        return [
            Observation(
                observation_id=_observation_id(
                    document.evidence_id,
                    session.calendar_date,
                    metric,
                ),
                source_evidence_id=document.evidence_id,
                source_path=document.source_path,
                metric=metric,
                value=value,
                unit=unit,
                observed_at=session.started_at,
                imported_at=self._imported_at,
                parser_name=self.name,
                parser_version=self.version,
            )
            for metric, value, unit in values
        ]

    def _failure(
        self,
        document: SourceDocument,
        code: str,
        message: str,
    ) -> ParseResult:
        return ParseResult(
            records=(),
            warnings=(),
            errors=(ParseMessage(code=code, message=message),),
            parser_name=self.name,
            parser_version=self.version,
            source_evidence_id=document.evidence_id,
        )


def _object(value: object, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError(f"{field} must be an object")
    return value


def _typed(
    source: dict[str, Any],
    field: str,
    predicate: Callable[[object], bool],
    expected: str,
) -> Any:
    if field not in source:
        raise KeyError(f"missing field {field}")
    value = source[field]
    if not predicate(value):
        raise TypeError(f"{field} must be {expected}")
    return value


def _integer(source: dict[str, Any], field: str) -> int:
    return _typed(
        source,
        field,
        lambda value: isinstance(value, int) and not isinstance(value, bool),
        "an integer",
    )


def _number(source: dict[str, Any], field: str) -> float:
    value = _typed(
        source,
        field,
        lambda item: isinstance(item, (int, float)) and not isinstance(item, bool),
        "a number",
    )
    return float(value)


def _string(source: dict[str, Any], field: str) -> str:
    return _typed(source, field, lambda value: isinstance(value, str), "a string")


def _boolean(source: dict[str, Any], field: str) -> bool:
    return _typed(source, field, lambda value: isinstance(value, bool), "a boolean")


def _date(source: dict[str, Any], field: str) -> date:
    try:
        return date.fromisoformat(_string(source, field))
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO date") from exc


def _timestamp(source: dict[str, Any], field: str) -> datetime:
    raw = _string(source, field)
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO timestamp") from exc
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


def _observation_id(evidence_id: str, day: date, metric: str) -> str:
    raw = f"{evidence_id}:{day.isoformat()}:{metric}".encode()
    return sha256(raw).hexdigest()
