from __future__ import annotations

import json
from pathlib import Path

import pytest

from crow_health.cli import main
from crow_health.runtime import runtime_identity


def test_runtime_identity_reports_supported_capabilities(tmp_path: Path) -> None:
    identity = runtime_identity(cwd=tmp_path)

    assert "version" in identity.capabilities
    assert "import-json-batch" in identity.capabilities
    assert identity.python_version
    assert identity.executable


def test_environment_commit_overrides_git(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("CROW_HEALTH_COMMIT", "verified-commit")

    identity = runtime_identity(cwd=tmp_path)

    assert identity.git_commit == "verified-commit"


def test_version_command_outputs_json(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("sys.argv", ["crow-health", "version"])

    assert main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["package_version"]
    assert "version" in payload["capabilities"]
