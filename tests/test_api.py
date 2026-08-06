from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from crow_health.api import API_VERSION, create_app
from crow_health.evidence.models import Observation
from crow_health.storage import JsonlObservationIndex, JsonlObservationStore


def _client(tmp_path: Path) -> TestClient:
    store_path = tmp_path / "observations.jsonl"
    JsonlObservationStore(store_path).append(
        (
            Observation(
                observation_id="stress-1",
                source_evidence_id="evidence-1",
                source_path="sample.json",
                metric="sleep.average_stress",
                value=20.0,
                unit=None,
                observed_at=datetime(2026, 8, 1, tzinfo=UTC),
                imported_at=datetime(2026, 8, 6, tzinfo=UTC),
                parser_name="garmin-sleep",
                parser_version="2",
            ),
            Observation(
                observation_id="stress-2",
                source_evidence_id="evidence-1",
                source_path="sample.json",
                metric="sleep.average_stress",
                value=24.0,
                unit=None,
                observed_at=datetime(2026, 8, 2, tzinfo=UTC),
                imported_at=datetime(2026, 8, 6, tzinfo=UTC),
                parser_name="garmin-sleep",
                parser_version="2",
            ),
        )
    )
    index_path = tmp_path / "observations.index.jsonl"
    JsonlObservationIndex(store_path, index_path).rebuild()
    return TestClient(create_app(store_path=store_path, index_path=index_path))


def test_health_exposes_versioned_read_only_runtime(tmp_path: Path) -> None:
    response = _client(tmp_path).get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["api_version"] == API_VERSION


def test_registry_filters_exact_metric(tmp_path: Path) -> None:
    response = _client(tmp_path).get(
        "/v1/registry",
        params={"metric": "sleep.average_stress"},
    )

    assert response.status_code == 200
    assert response.json()[0]["metric"] == "sleep.average_stress"
    assert response.json()[0]["category"] == "sleep"


def test_unknown_registry_metric_returns_404(tmp_path: Path) -> None:
    response = _client(tmp_path).get("/v1/registry", params={"metric": "missing"})

    assert response.status_code == 404


def test_statistics_reuses_existing_service(tmp_path: Path) -> None:
    response = _client(tmp_path).get("/v1/statistics/sleep.average_stress")

    assert response.status_code == 200
    assert response.json()["count"] == 2
    assert response.json()["mean"] == 22.0


def test_snapshot_accepts_repeated_metric_parameters(tmp_path: Path) -> None:
    response = _client(tmp_path).get(
        "/v1/snapshot",
        params=[
            ("metric", "sleep.average_stress"),
            ("metric", "sleep.score.overall"),
        ],
    )

    assert response.status_code == 200
    assert response.json()["schema_version"] == "crow-health.snapshot.v1"
    assert [item["metric"] for item in response.json()["metrics"]] == [
        "sleep.average_stress",
        "sleep.score.overall",
    ]


def test_timeline_filters_by_metric_prefix(tmp_path: Path) -> None:
    response = _client(tmp_path).get(
        "/v1/timeline",
        params={"metric_prefix": "sleep.average_"},
    )

    assert response.status_code == 200
    assert response.json()["observation_count"] == 2
