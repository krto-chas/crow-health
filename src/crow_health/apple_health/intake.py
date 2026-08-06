from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from crow_health.apple_health.manifest import load_manifest_payload


@dataclass(frozen=True, slots=True)
class ManifestIntakeResult:
    evidence_id: str
    path: str
    entry_count: int
    existing: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "path": self.path,
            "entry_count": self.entry_count,
            "existing": self.existing,
        }


class AppleHealthManifestIntake:
    def __init__(self, root: Path, token: str) -> None:
        if not token:
            raise ValueError("A non-empty intake token is required")
        self._root = root
        self._token = token

    def authorize(self, authorization: str | None) -> None:
        prefix = "Bearer "
        supplied = authorization[len(prefix):] if authorization and authorization.startswith(prefix) else ""
        if not hmac.compare_digest(supplied, self._token):
            raise PermissionError("Invalid intake token")

    def ingest(self, payload: dict[str, Any]) -> ManifestIntakeResult:
        entries = load_manifest_payload(payload)
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        evidence_id = hashlib.sha256(canonical).hexdigest()
        destination = self._root / f"{evidence_id}.json"
        existing = destination.exists()
        if not existing:
            self._root.mkdir(parents=True, exist_ok=True)
            temporary = destination.with_suffix(".tmp")
            temporary.write_bytes(canonical)
            temporary.replace(destination)
        return ManifestIntakeResult(evidence_id, str(destination), len(entries), existing)
