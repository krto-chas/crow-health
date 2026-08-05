from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from crow_health.storage import JsonlObservationIndex, JsonlObservationStore


@dataclass(frozen=True, slots=True)
class StoreValidationReport:
    store: str
    index: str
    observation_count: int
    index_entry_count: int
    metric_counts: dict[str, int]
    parser_counts: dict[str, int]
    source_count: int
    observations_without_timestamp: int
    observed_from: datetime | None
    observed_to: datetime | None
    index_matches_store: bool

    @property
    def succeeded(self) -> bool:
        return self.index_matches_store

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["observed_from"] = self.observed_from.isoformat() if self.observed_from else None
        value["observed_to"] = self.observed_to.isoformat() if self.observed_to else None
        value["succeeded"] = self.succeeded
        return value


def validate_store(
    store_path: Path,
    index_path: Path | None = None,
    *,
    rebuild_index: bool = True,
) -> StoreValidationReport:
    store = JsonlObservationStore(store_path)
    observations = store.all()
    index = JsonlObservationIndex(store_path, index_path)
    if rebuild_index:
        index.rebuild()
    entries = index.entries()

    timestamps = tuple(
        observation.observed_at
        for observation in observations
        if observation.observed_at is not None
    )
    observation_ids = tuple(item.observation_id for item in observations)
    index_ids = tuple(item.observation_id for item in entries)

    return StoreValidationReport(
        store=str(store_path),
        index=str(index.index_path),
        observation_count=len(observations),
        index_entry_count=len(entries),
        metric_counts=dict(sorted(Counter(item.metric for item in observations).items())),
        parser_counts=dict(
            sorted(Counter(item.parser_name for item in observations).items())
        ),
        source_count=len({item.source_evidence_id for item in observations}),
        observations_without_timestamp=sum(
            item.observed_at is None for item in observations
        ),
        observed_from=min(timestamps) if timestamps else None,
        observed_to=max(timestamps) if timestamps else None,
        index_matches_store=observation_ids == index_ids,
    )
