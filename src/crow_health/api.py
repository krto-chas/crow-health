from __future__ import annotations

import os
from dataclasses import asdict
from datetime import date, datetime
from pathlib import Path
from typing import Annotated, Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.encoders import jsonable_encoder

from crow_health.analytics import AnalyticsService
from crow_health.catalog import CatalogQuery, ObservationCatalog
from crow_health.registry import UnknownMetricError, default_metric_registry
from crow_health.runtime import runtime_identity
from crow_health.snapshot import SnapshotQuery, SnapshotService
from crow_health.statistics import DescriptiveStatistics, StatisticsQuery
from crow_health.storage import JsonlObservationIndex, JsonlObservationStore
from crow_health.timeline import ObservationTimeline, TimelineQuery

API_VERSION = "crow-health.api.v1"


def create_app(
    *,
    store_path: Path | None = None,
    index_path: Path | None = None,
) -> FastAPI:
    store = store_path or Path(os.getenv("CROW_HEALTH_STORE", "data/observations.jsonl"))
    configured_index = index_path or _optional_path(os.getenv("CROW_HEALTH_INDEX"))
    registry = default_metric_registry()
    observation_store = JsonlObservationStore(store)
    observation_index = JsonlObservationIndex(store, configured_index)
    timeline = ObservationTimeline(observation_index)
    statistics = DescriptiveStatistics(timeline)
    analytics = AnalyticsService(statistics)
    snapshots = SnapshotService(statistics, analytics, registry)

    app = FastAPI(
        title="Crow Health API",
        version=API_VERSION,
        description="Read-only access to normalized Crow Health data and derived views.",
    )

    @app.get("/health")
    def health() -> dict[str, Any]:
        identity = runtime_identity()
        return {
            "status": "ok",
            "api_version": API_VERSION,
            "runtime": identity.to_dict(),
        }

    @app.get("/v1/registry")
    def metric_registry(
        category: str | None = None,
        metric: str | None = None,
    ) -> Any:
        definitions = registry.list(category=category, metric=metric)
        if metric is not None and not definitions:
            raise HTTPException(status_code=404, detail=f"Unknown metric: {metric}")
        return jsonable_encoder([asdict(item) for item in definitions])

    @app.get("/v1/catalog")
    def catalog(
        metric_prefix: str | None = None,
        source_evidence_id: str | None = None,
        parser_name: str | None = None,
    ) -> Any:
        result = ObservationCatalog(observation_store).build(
            CatalogQuery(
                metric_prefix=metric_prefix,
                source_evidence_id=source_evidence_id,
                parser_name=parser_name,
            )
        )
        return jsonable_encoder(asdict(result))

    @app.get("/v1/timeline")
    def timeline_query(
        day: date | None = None,
        observed_from: datetime | None = Query(default=None, alias="from"),
        observed_to: datetime | None = Query(default=None, alias="to"),
        source_evidence_id: str | None = None,
        parser_name: str | None = None,
        metric_prefix: str | None = None,
    ) -> Any:
        result = timeline.query(
            TimelineQuery(
                day=day,
                observed_from=observed_from,
                observed_to=observed_to,
                source_evidence_id=source_evidence_id,
                parser_name=parser_name,
                metric_prefix=metric_prefix,
            )
        )
        return jsonable_encoder(asdict(result))

    @app.get("/v1/statistics/{metric}")
    def metric_statistics(
        metric: str,
        observed_from: datetime | None = Query(default=None, alias="from"),
        observed_to: datetime | None = Query(default=None, alias="to"),
        source_evidence_id: str | None = None,
        parser_name: str | None = None,
    ) -> Any:
        _require_metric(metric)
        result = statistics.summarize(
            StatisticsQuery(
                metric=metric,
                observed_from=observed_from,
                observed_to=observed_to,
                source_evidence_id=source_evidence_id,
                parser_name=parser_name,
            )
        )
        return jsonable_encoder(asdict(result))

    @app.get("/v1/snapshot")
    def snapshot(
        metric: Annotated[list[str], Query()],
        observed_from: datetime | None = Query(default=None, alias="from"),
        observed_to: datetime | None = Query(default=None, alias="to"),
        source_evidence_id: str | None = None,
        parser_name: str | None = None,
        window_days: int = Query(default=7, ge=1),
    ) -> Any:
        try:
            result = snapshots.build(
                SnapshotQuery(
                    metrics=tuple(metric),
                    observed_from=observed_from,
                    observed_to=observed_to,
                    source_evidence_id=source_evidence_id,
                    parser_name=parser_name,
                    moving_average_window_days=window_days,
                )
            )
        except UnknownMetricError as exc:
            raise HTTPException(status_code=404, detail=f"Unknown metric: {exc.args[0]}") from exc
        return jsonable_encoder(result.to_dict())

    def _require_metric(metric: str) -> None:
        try:
            registry.get(metric)
        except UnknownMetricError as exc:
            raise HTTPException(status_code=404, detail=f"Unknown metric: {metric}") from exc

    return app


def _optional_path(value: str | None) -> Path | None:
    return Path(value) if value else None


app = create_app()
