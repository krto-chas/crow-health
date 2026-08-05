from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from crow_health.evidence.models import Observation
from crow_health.storage.observations import _from_dict


@dataclass(frozen=True, slots=True)
class ObservationIndexEntry:
    observation_id: str
    metric: str
    source_evidence_id: str
    source_path: str
    parser_name: str
    observed_at: datetime | None
    byte_offset: int
    byte_length: int


@dataclass(frozen=True, slots=True)
class ObservationQuery:
    metric: str | None = None
    source_evidence_id: str | None = None
    parser_name: str | None = None
    observed_from: datetime | None = None
    observed_to: datetime | None = None


class JsonlObservationIndex:
    """Rebuildable metadata index for an append-only JSONL observation store."""

    def __init__(self, store_path: Path, index_path: Path | None = None) -> None:
        self._store_path = store_path
        self._index_path = index_path or store_path.with_suffix(store_path.suffix + ".index")

    @property
    def index_path(self) -> Path:
        return self._index_path

    def rebuild(self) -> int:
        entries = self._scan_store()
        self._index_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self._index_path.with_suffix(self._index_path.suffix + ".tmp")
        try:
            with temporary.open("w", encoding="utf-8", newline="\n") as handle:
                for entry in entries:
                    handle.write(json.dumps(_entry_to_dict(entry), sort_keys=True))
                    handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            temporary.replace(self._index_path)
        finally:
            if temporary.exists():
                temporary.unlink()
        return len(entries)

    def entries(self) -> tuple[ObservationIndexEntry, ...]:
        if not self._index_path.exists():
            return ()
        result: list[ObservationIndexEntry] = []
        seen: set[str] = set()
        with self._index_path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                entry = _entry_from_dict(json.loads(line))
                if entry.observation_id in seen:
                    raise ValueError(
                        f"Duplicate observation ID in index at line {line_number}: "
                        f"{entry.observation_id}"
                    )
                seen.add(entry.observation_id)
                result.append(entry)
        return tuple(result)

    def query(self, query: ObservationQuery) -> tuple[Observation, ...]:
        matches = tuple(entry for entry in self.entries() if _matches(entry, query))
        if not matches or not self._store_path.exists():
            return ()

        observations: list[Observation] = []
        with self._store_path.open("rb") as handle:
            for entry in matches:
                handle.seek(entry.byte_offset)
                payload = handle.read(entry.byte_length)
                observation = _from_dict(json.loads(payload.decode("utf-8")))
                if observation.observation_id != entry.observation_id:
                    raise ValueError(
                        "Observation index does not match the current store content: "
                        f"{entry.observation_id}"
                    )
                observations.append(observation)
        return tuple(observations)

    def _scan_store(self) -> tuple[ObservationIndexEntry, ...]:
        if not self._store_path.exists():
            return ()

        entries: list[ObservationIndexEntry] = []
        seen: set[str] = set()
        with self._store_path.open("rb") as handle:
            while True:
                offset = handle.tell()
                line = handle.readline()
                if not line:
                    break
                if not line.strip():
                    continue
                observation = _from_dict(json.loads(line.decode("utf-8")))
                if observation.observation_id in seen:
                    raise ValueError(
                        "Duplicate observation ID in store while rebuilding index: "
                        f"{observation.observation_id}"
                    )
                seen.add(observation.observation_id)
                entries.append(
                    ObservationIndexEntry(
                        observation_id=observation.observation_id,
                        metric=observation.metric,
                        source_evidence_id=observation.source_evidence_id,
                        source_path=observation.source_path,
                        parser_name=observation.parser_name,
                        observed_at=observation.observed_at,
                        byte_offset=offset,
                        byte_length=len(line),
                    )
                )
        return tuple(entries)


def _matches(entry: ObservationIndexEntry, query: ObservationQuery) -> bool:
    if query.metric is not None and entry.metric != query.metric:
        return False
    if (
        query.source_evidence_id is not None
        and entry.source_evidence_id != query.source_evidence_id
    ):
        return False
    if query.parser_name is not None and entry.parser_name != query.parser_name:
        return False
    if (
        query.observed_from is not None
        and (entry.observed_at is None or entry.observed_at < query.observed_from)
    ):
        return False
    if (
        query.observed_to is not None
        and (entry.observed_at is None or entry.observed_at > query.observed_to)
    ):
        return False
    return True


def _entry_to_dict(entry: ObservationIndexEntry) -> dict[str, object]:
    value = asdict(entry)
    value["observed_at"] = entry.observed_at.isoformat() if entry.observed_at else None
    return value


def _entry_from_dict(value: object) -> ObservationIndexEntry:
    if not isinstance(value, dict):
        raise TypeError("Stored index entry must be a JSON object")
    observed_at = value.get("observed_at")
    if observed_at is not None and not isinstance(observed_at, str):
        raise TypeError("Stored index field observed_at must be a string or null")
    return ObservationIndexEntry(
        observation_id=_required_string(value, "observation_id"),
        metric=_required_string(value, "metric"),
        source_evidence_id=_required_string(value, "source_evidence_id"),
        source_path=_required_string(value, "source_path"),
        parser_name=_required_string(value, "parser_name"),
        observed_at=datetime.fromisoformat(observed_at) if observed_at else None,
        byte_offset=_required_int(value, "byte_offset"),
        byte_length=_required_int(value, "byte_length"),
    )


def _required_string(source: dict[object, object], field: str) -> str:
    value = source.get(field)
    if not isinstance(value, str):
        raise TypeError(f"Stored index field {field} must be a string")
    return value


def _required_int(source: dict[object, object], field: str) -> int:
    value = source.get(field)
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"Stored index field {field} must be an integer")
    return value
