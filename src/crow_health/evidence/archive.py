from __future__ import annotations

import hashlib
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

from crow_health.evidence.models import EvidenceFile


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def archive_file(source: Path, evidence_root: Path) -> EvidenceFile:
    if not source.is_file():
        raise FileNotFoundError(source)
    digest = sha256_file(source)
    evidence_id = digest[:16]
    target_dir = evidence_root / "raw" / evidence_id
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / source.name
    if target.exists() and sha256_file(target) != digest:
        raise RuntimeError(f"Archive collision: {target}")
    if not target.exists():
        shutil.copy2(source, target)
    evidence = EvidenceFile(
        evidence_id=evidence_id,
        source_name=source.name,
        sha256=digest,
        size_bytes=source.stat().st_size,
        archived_path=str(target),
        imported_at=datetime.now(UTC),
    )
    manifest = target_dir / "manifest.json"
    if not manifest.exists():
        manifest.write_text(json.dumps(evidence.to_dict(), indent=2, sort_keys=True) + "\n")
    return evidence
