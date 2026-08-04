from __future__ import annotations

import json
from pathlib import Path

from crow_health.cli import main
from crow_health.runtime import runtime_identity


def test_runtime_identity_reports_supported_capabilities(tmp_path: Path) -> None:
    identity = runtime_identity(cwd=tmp_path)

    assert "version" in identity.capabilities
    assert "import-json-batch" in identity.capabilities
    assert identity.python_version
    assert identity.executable


def test_environment_commit_overrides_git(monkeypatch: object, tmp_path: Path) -> None:
    monkeypatch.setenv("CROW_HEALTH_COMMIT", "verified-commit")  # type: ignore[attr-defined]

    identity = runtime_identity(cwd=tmp_path)

    assert identity.git_commit == "verified-commit"


def test_version_command_outputs_json(monkeypatch: object, capsys: object) -> None:
    monkeypatch.setattr("sys.argv", ["crow-health", "version"])  # type: ignore[attr-defined]

    assert main() == 0
    output = capsys.readouterr().out  # type: ignore[attr-defined]
    payload = json.loads(output)
    assert payload["package_version"]
    assert "version" in payload["capabilities"]
