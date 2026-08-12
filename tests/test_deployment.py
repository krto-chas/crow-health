import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_uvicorn_is_declared_as_runtime_dependency() -> None:
    payload = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = payload["project"]["dependencies"]

    assert any(item.startswith("uvicorn") for item in dependencies)


def test_dockerfile_runs_read_only_api_with_uvicorn() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "python:3.13-slim" in dockerfile
    assert '"uvicorn", "crow_health.api:app"' in dockerfile
    assert '"--host", "0.0.0.0"' in dockerfile
    assert '"--port", "8000"' in dockerfile


def test_compose_uses_persistent_crow_health_paths() -> None:
    compose = (ROOT / "compose.yaml").read_text(encoding="utf-8")

    assert "/srv/crow-data/health:/srv/crow-data/health" in compose
    assert "/srv/crow-data/health/observations/observations.jsonl" in compose
    assert "/srv/crow-data/health/observations/observations.index.jsonl" in compose
    assert "/srv/crow-data/health/evidence/apple-health-manifests" in compose


def test_compose_defaults_to_loopback_and_non_root_numeric_user() -> None:
    compose = (ROOT / "compose.yaml").read_text(encoding="utf-8")

    assert "CROW_HEALTH_BIND_ADDRESS:-127.0.0.1" in compose
    assert 'user: "${CROW_HEALTH_UID:-1000}:${CROW_HEALTH_GID:-1000}"' in compose
    assert "restart: unless-stopped" in compose


def test_no_secret_is_committed_in_environment_template() -> None:
    environment = (ROOT / ".env.example").read_text(encoding="utf-8")

    assert "CROW_HEALTH_APPLE_MANIFEST_TOKEN=\n" in environment
