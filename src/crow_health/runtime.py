from __future__ import annotations

import os
import platform
import subprocess
import sys
from dataclasses import asdict, dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class RuntimeIdentity:
    package_version: str
    git_commit: str | None
    python_version: str
    platform: str
    executable: str
    project_root: str | None
    capabilities: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def runtime_identity(*, cwd: Path | None = None) -> RuntimeIdentity:
    root = _git_root(cwd)
    return RuntimeIdentity(
        package_version=_package_version(),
        git_commit=os.environ.get("CROW_HEALTH_COMMIT") or _git_commit(root),
        python_version=platform.python_version(),
        platform=platform.system(),
        executable=sys.executable,
        project_root=str(root) if root is not None else None,
        capabilities=(
            "archive-export",
            "inventory-export",
            "profile-export",
            "inspect-json",
            "import-json-member",
            "import-json-batch",
            "version",
        ),
    )


def _package_version() -> str:
    try:
        return version("crow-health")
    except PackageNotFoundError:
        return "uninstalled"


def _git_root(cwd: Path | None) -> Path | None:
    return _git_value(("rev-parse", "--show-toplevel"), cwd=cwd, as_path=True)


def _git_commit(root: Path | None) -> str | None:
    if root is None:
        return None
    value = _git_value(("rev-parse", "HEAD"), cwd=root)
    return value if isinstance(value, str) else None


def _git_value(
    arguments: tuple[str, ...],
    *,
    cwd: Path | None,
    as_path: bool = False,
) -> str | Path | None:
    try:
        result = subprocess.run(
            ("git", *arguments),
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (FileNotFoundError, subprocess.SubprocessError):
        return None
    value = result.stdout.strip()
    if not value:
        return None
    return Path(value) if as_path else value
