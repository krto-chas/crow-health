from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, date, datetime
from hashlib import sha256
from typing import Any, cast

from crow_health.domain.sleep import SleepRespiration, SleepScore, SleepSession, SleepStages
from crow_health.evidence.models import Observation
from crow_health.parsers.models import ParseMessage, ParseResult, SourceDocument


class GarminSleepParser:
    name = "garmin-sleep"
    version = "2"
    supported_path_patterns: tuple[str, ...] = ("*sleepData.json",)
    supported_media_types: tuple[str, ...] = ("application/json",)

    def __init__(self, *, imported_at: datetime | None = None) -> None:
        self._imported_at = imported_at or datetime.now(UTC)

    def parse(self, document: SourceDocument) -> ParseResult:
        if not isinstance(document.payload, list):
            return self._failure(document, "root_type", "Expected a JSON array")

        observations: list[Observation] = []
        warnings: list[ParseMessage] = []
        errors: list[ParseMessage] = []
        for index, raw in enumerate(document.payload):
            try:
                session, record_warnings = self.parse_session(raw)
            except (KeyError, TypeError, ValueError) as exc:
                errors.append(ParseMessage(code="invalid_sleep_record", message=f"Record {index}: {exc}"))
                continue
            observations.extend(self._observations(document, session))
            warnings.extend(
                ParseMessage(code=code, message=f"Record {index}: {message}")
                for code, message in record_warnings
            )

        return ParseResult(
            records=tuple(observations),
            warnings=tuple(warnings),
            errors=tuple(errors),
            parser_name=self.name,
            parser_version=self.version,
            source_evidence_id=document.evidence_id,
        )

    def parse_session(self, raw: object) -> tuple[SleepSession, tuple[tuple[str, str], ...]]:
        record = _object(raw, "record")
        warnings: list[tuple[str, str]] = []
        raw_scores = record.get("sleepScores")
        scores = raw_scores if isinstance(raw_scores, dict) else None
        if scores is None:
            warnings.append(("legacy_sleep_scores_unavailable", "sleepScores is absent or not an object; score observations were omitted"))

        session = SleepSession(
            calendar_date=_date(record, "calendarDate"),
            started_at=_timestamp(record, "sleepStartTimestampGMT"),
            ended_at=_timestamp(record, "sleepEndTimestampGMT"),
            stages=SleepStages(
                awake_seconds=_optional_integer(record, "awakeSleepSeconds"),
                deep_seconds=_optional_integer(record, "deepSleepSeconds"),
                light_seconds=_optional_integer(record, "lightSleepSeconds"),
                rem_seconds=_optional_integer(record, "remSleepSeconds"),
                unmeasurable_seconds=_optional_integer(record, "unmeasurableSeconds"),
            ),
            respiration=SleepRespiration(
                average=_optional_number(record, "averageRespiration"),
                highest=_optional_number(record, "highestRespiration"),
                lowest=_optional_number(record, "lowestRespiration"),
            ),
            score=_sleep_score(scores),
            average_stress=_optional_number(record, "avgSleepStress"),
            awake_count=_optional_integer(record, "awakeCount"),
            restless_moment_count=_optional_integer(record, "restlessMomentCount"),
            retro=_optional_boolean(record, "retro"),
            confirmation_type=_optional_string(record, "sleepWindowConfirmationType"),
        )
        return session, tuple(warnings)

    def _observations(self, document: SourceDocument, session: SleepSession) -> list[Observation]:
        values: list[tuple[str, int | float | str | bool | None, str | None]] = [
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
            ("sleep.retro", session.retro, None),
            ("sleep.confirmation_type", session.confirmation_type, None),
        ]
        if session.score is not None:
            values.extend(
                (
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
                )
            )
        return [
            Observation(
                observation_id=_observation_id(document.evidence_id, session.calendar_date, metric),
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
            if value is not None
        ]

    def _failure(self, document: SourceDocument, code: str, message: str) -> ParseResult:
        return ParseResult(records=(), warnings=(), errors=(ParseMessage(code=code, message=message),), parser_name=self.name, parser_version=self.version, source_evidence_id=document.evidence_id)


def _sleep_score(scores: dict[str, Any] | None) -> SleepScore | None:
    if scores is None:
        return None
    return SleepScore(
        overall=_optional_integer(scores, "overallScore"),
        quality=_optional_integer(scores, "qualityScore"),
        recovery=_optional_integer(scores, "recoveryScore"),
        duration=_optional_integer(scores, "durationScore"),
        deep=_optional_integer(scores, "deepScore"),
        rem=_optional_integer(scores, "remScore"),
        light=_optional_integer(scores, "lightScore"),
        restfulness=_optional_integer(scores, "restfulnessScore"),
        awake_time=_optional_integer(scores, "awakeTimeScore"),
        awakenings_count=_optional_integer(scores, "awakeningsCountScore"),
        combined_awake=_optional_integer(scores, "combinedAwakeScore"),
        interruptions=_optional_integer(scores, "interruptionsScore"),
        feedback=_optional_string(scores, "feedback"),
        insight=_optional_string(scores, "insight"),
    )


def _object(value: object, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError(f"{field} must be an object")
    return value


def _typed(source: dict[str, Any], field: str, predicate: Callable[[object], bool], expected: str) -> Any:
    if field not in source:
        raise KeyError(f"missing field {field}")
    value = source[field]
    if not predicate(value):
        raise TypeError(f"{field} must be {expected}")
    return value


def _integer(source: dict[str, Any], field: str) -> int:
    value = _typed(source, field, lambda item: isinstance(item, int) and not isinstance(item, bool), "an integer")
    return cast(int, value)


def _optional_integer(source: dict[str, Any], field: str) -> int | None:
    return None if field not in source or source[field] is None else _integer(source, field)


def _number(source: dict[str, Any], field: str) -> float:
    value = _typed(source, field, lambda item: isinstance(item, (int, float)) and not isinstance(item, bool), "a number")
    return float(value)


def _optional_number(source: dict[str, Any], field: str) -> float | None:
    return None if field not in source or source[field] is None else _number(source, field)


def _string(source: dict[str, Any], field: str) -> str:
    value = _typed(source, field, lambda item: isinstance(item, str), "a string")
    return cast(str, value)


def _optional_string(source: dict[str, Any], field: str) -> str | None:
    return None if field not in source or source[field] is None else _string(source, field)


def _boolean(source: dict[str, Any], field: str) -> bool:
    value = _typed(source, field, lambda item: isinstance(item, bool), "a boolean")
    return cast(bool, value)


def _optional_boolean(source: dict[str, Any], field: str) -> bool | None:
    return None if field not in source or source[field] is None else _boolean(source, field)


def _date(source: dict[str, Any], field: str) -> date:
    try:
        return date.fromisoformat(_string(source, field))
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO date") from exc


def _timestamp(source: dict[str, Any], field: str) -> datetime:
    raw = _string(source, field)
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO timestamp") from exc
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


def _observation_id(evidence_id: str, day: date, metric: str) -> str:
    return sha256(f"{evidence_id}:{day.isoformat()}:{metric}".encode()).hexdigest()
