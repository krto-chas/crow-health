from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from crow_health.evidence.models import Observation
from crow_health.storage import ObservationStore


@dataclass(frozen=True, slots=True)
class CatalogQuery:
    metric_prefix: str | None = None
    parser_name: str | None = None
    source_evidence_id: str | None = None


@dataclass(frozen=True, slots=True)
class MetricCatalogEntry:
    metric: str
    observation_count: int
    timestamped_count: int
    covered_days: int
    first_observed_at: datetime | None
    last_observed_at: datetime | None
    value_types: tuple[str, ...]
    units: tuple[str | None, ...]
    parser_names: tuple[str, ...]
    source_evidence_count: int
    numeric_observation_count: int
    statistics_supported: bool


@dataclass(frozen=True, slots=True)
class ObservationCatalogResult:
    metrics: tuple[MetricCatalogEntry, ...]
    metric_count: int
    observation_count: int


class ObservationCatalog:
    """Deterministic inventory of metrics present in the authoritative store."""

    def __init__(self, store: ObservationStore) -> None:
        self._store = store

    def build(self, query: CatalogQuery | None = None) -> ObservationCatalogResult:
        resolved = query or CatalogQuery()
        grouped: dict[str, list[Observation]] = {}
        for observation in self._store.all():
            if resolved.metric_prefix is not None and not observation.metric.startswith(
                resolved.metric_prefix
            ):
                continue
            if (
                resolved.parser_name is not None
                and observation.parser_name != resolved.parser_name
            ):
                continue
            if (
                resolved.source_evidence_id is not None
                and observation.source_evidence_id != resolved.source_evidence_id
            ):
                continue
            grouped.setdefault(observation.metric, []).append(observation)

        entries = tuple(
            _entry(metric, tuple(observations))
            for metric, observations in sorted(grouped.items())
        )
        return ObservationCatalogResult(
            metrics=entries,
            metric_count=len(entries),
            observation_count=sum(entry.observation_count for entry in entries),
        )


def _entry(metric: str, observations: tuple[Observation, ...]) -> MetricCatalogEntry:
    timestamps = tuple(
        observation.observed_at
        for observation in observations
        if observation.observed_at is not None
    )
    days: set[date] = {timestamp.date() for timestamp in timestamps}
    value_types = tuple(sorted({_value_type(observation.value) for observation in observations}))
    units = tuple(sorted({observation.unit for observation in observations}, key=_unit_key))
    numeric_count = sum(_is_numeric(observation.value) for observation in observations)
    statistics_supported = (
        numeric_count == len(observations)
        and len(units) <= 1
        and bool(observations)
    )
    return MetricCatalogEntry(
        metric=metric,
        observation_count=len(observations),
        timestamped_count=len(timestamps),
        covered_days=len(days),
        first_observed_at=min(timestamps) if timestamps else None,
        last_observed_at=max(timestamps) if timestamps else None,
        value_types=value_types,
        units=units,
        parser_names=tuple(sorted({item.parser_name for item in observations})),
        source_evidence_count=len({item.source_evidence_id for item in observations}),
        numeric_observation_count=numeric_count,
        statistics_supported=statistics_supported,
    )


def _is_numeric(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _value_type(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    raise TypeError(f"Unsupported observation value type: {type(value).__name__}")


def _unit_key(unit: str | None) -> tuple[int, str]:
    return (0, "") if unit is None else (1, unit)
