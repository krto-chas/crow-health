from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time

from crow_health.evidence.models import Observation
from crow_health.storage import JsonlObservationIndex, ObservationQuery


@dataclass(frozen=True, slots=True)
class TimelineQuery:
    observed_from: datetime | None = None
    observed_to: datetime | None = None
    day: date | None = None
    source_evidence_id: str | None = None
    parser_name: str | None = None
    metric_prefix: str | None = None


@dataclass(frozen=True, slots=True)
class TimelineGroup:
    group_id: str
    observed_at: datetime
    source_evidence_id: str
    parser_name: str
    observations: tuple[Observation, ...]


@dataclass(frozen=True, slots=True)
class TimelineResult:
    groups: tuple[TimelineGroup, ...]
    observation_count: int
    excluded_without_timestamp: int


class ObservationTimeline:
    """Time-ordered view over indexed observations without changing evidence storage."""

    def __init__(self, index: JsonlObservationIndex) -> None:
        self._index = index

    def query(self, query: TimelineQuery) -> TimelineResult:
        observed_from, observed_to = _resolved_range(query)
        observations = self._index.query(
            ObservationQuery(
                source_evidence_id=query.source_evidence_id,
                parser_name=query.parser_name,
                observed_from=observed_from,
                observed_to=observed_to,
            )
        )

        timestamped: list[Observation] = []
        excluded = 0
        for observation in observations:
            if observation.observed_at is None:
                excluded += 1
                continue
            if query.metric_prefix is not None and not observation.metric.startswith(
                query.metric_prefix
            ):
                continue
            timestamped.append(observation)

        grouped: dict[tuple[datetime, str, str], list[Observation]] = {}
        for observation in timestamped:
            assert observation.observed_at is not None
            key = (
                observation.observed_at,
                observation.source_evidence_id,
                observation.parser_name,
            )
            grouped.setdefault(key, []).append(observation)

        groups = tuple(
            TimelineGroup(
                group_id=_group_id(observed_at, evidence_id, parser_name),
                observed_at=observed_at,
                source_evidence_id=evidence_id,
                parser_name=parser_name,
                observations=tuple(
                    sorted(items, key=lambda item: (item.metric, item.observation_id))
                ),
            )
            for (observed_at, evidence_id, parser_name), items in sorted(
                grouped.items(), key=lambda item: item[0]
            )
        )
        return TimelineResult(
            groups=groups,
            observation_count=sum(len(group.observations) for group in groups),
            excluded_without_timestamp=excluded,
        )


def _resolved_range(query: TimelineQuery) -> tuple[datetime | None, datetime | None]:
    if query.day is None:
        return query.observed_from, query.observed_to
    if query.observed_from is not None or query.observed_to is not None:
        raise ValueError("day cannot be combined with observed_from or observed_to")
    start = datetime.combine(query.day, time.min, tzinfo=UTC)
    end = datetime.combine(query.day, time.max, tzinfo=UTC)
    return start, end


def _group_id(observed_at: datetime, evidence_id: str, parser_name: str) -> str:
    return f"{observed_at.isoformat()}:{evidence_id}:{parser_name}"
