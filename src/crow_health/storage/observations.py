from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol

from crow_health.evidence.models import Observation


class ObservationConflictError(ValueError):
    """Raised when one observation ID refers to different content."""


@dataclass(frozen=True, slots=True)
class StoreResult:
    inserted: int
    existing: int


class ObservationStore(Protocol):
    def append(self, observations: tuple[Observation, ...]) -> StoreResult: ...

    def get(self, observation_id: str) -> Observation | None: ...

    def all(self) -> tuple[Observation, ...]: ...


class JsonlObservationStore:
    """Append-only local observation store with idempotent writes."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def append(self, observations: tuple[Observation, ...]) -> StoreResult:
        current = {item.observation_id: item for item in self.all()}
        pending: list[Observation] = []
        existing = 0

        for observation in observations:
            stored = current.get(observation.observation_id)
            if stored is None:
                current[observation.observation_id] = observation
                pending.append(observation)
                continue
            if stored != observation:
                raise ObservationConflictError(
                    f"Observation ID has conflicting content: {observation.observation_id}"
                )
            existing += 1

        if pending:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._path.open("a", encoding="utf-8", newline="\n") as handle:
                for observation in pending:
                    handle.write(json.dumps(_to_dict(observation), sort_keys=True))
                    handle.write("\n")

        return StoreResult(inserted=len(pending), existing=existing)

    def get(self, observation_id: str) -> Observation | None:
        return next(
            (item for item in self.all() if item.observation_id == observation_id),
            None,
        )

    def all(self) -> tuple[Observation, ...]:
        if not self._path.exists():
            return ()

        observations: list[Observation] = []
        seen: set[str] = set()
        with self._path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                observation = _from_dict(json.loads(line))
                if observation.observation_id in seen:
                    raise ObservationConflictError(
                        f"Duplicate observation ID in store at line {line_number}: "
                        f"{observation.observation_id}"
                    )
                seen.add(observation.observation_id)
                observations.append(observation)
        return tuple(observations)


def _to_dict(observation: Observation) -> dict[str, object]:
    value = asdict(observation)
    value["observed_at"] = (
        observation.observed_at.isoformat() if observation.observed_at else None
    )
    value["imported_at"] = observation.imported_at.isoformat()
    return value


def _from_dict(value: object) -> Observation:
    if not isinstance(value, dict):
        raise TypeError("Stored observation must be a JSON object")

    return Observation(
        observation_id=_string(value, "observation_id"),
        source_evidence_id=_string(value, "source_evidence_id"),
        source_path=_string(value, "source_path"),
        metric=_string(value, "metric"),
        value=_observation_value(value.get("value")),
        unit=_optional_string(value, "unit"),
        observed_at=_optional_datetime(value, "observed_at"),
        imported_at=_datetime(value, "imported_at"),
        parser_name=_string(value, "parser_name"),
        parser_version=_string(value, "parser_version"),
    )


def _string(source: dict[object, object], field: str) -> str:
    value = source.get(field)
    if not isinstance(value, str):
        raise TypeError(f"Stored field {field} must be a string")
    return value


def _optional_string(source: dict[object, object], field: str) -> str | None:
    value = source.get(field)
    if value is None or isinstance(value, str):
        return value
    raise TypeError(f"Stored field {field} must be a string or null")


def _datetime(source: dict[object, object], field: str) -> datetime:
    try:
        return datetime.fromisoformat(_string(source, field))
    except ValueError as exc:
        raise ValueError(f"Stored field {field} must be an ISO timestamp") from exc


def _optional_datetime(source: dict[object, object], field: str) -> datetime | None:
    value = source.get(field)
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"Stored field {field} must be a string or null")
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"Stored field {field} must be an ISO timestamp") from exc


def _observation_value(value: object) -> int | float | str | bool | None:
    if value is None or isinstance(value, (int, float, str, bool)):
        return value
    raise TypeError("Stored observation value has an unsupported type")
