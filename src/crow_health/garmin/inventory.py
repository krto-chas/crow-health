from __future__ import annotations

import hashlib
import json
import zipfile
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any


@dataclass(frozen=True, slots=True)
class InventoryEntry:
    path: str
    size_bytes: int
    suffix: str
    sha256: str | None


@dataclass(frozen=True, slots=True)
class ExportInventory:
    source_type: str
    file_count: int
    total_bytes: int
    suffix_counts: dict[str, int]
    entries: tuple[InventoryEntry, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"source_type": self.source_type, "file_count": self.file_count,
                "total_bytes": self.total_bytes, "suffix_counts": self.suffix_counts,
                "entries": [asdict(entry) for entry in self.entries]}


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def inventory_zip(path: Path, hash_limit_bytes: int = 10 * 1024 * 1024) -> ExportInventory:
    if not path.is_file() or not zipfile.is_zipfile(path):
        raise ValueError(f"Expected ZIP archive: {path}")
    entries: list[InventoryEntry] = []
    with zipfile.ZipFile(path) as archive:
        for info in sorted(archive.infolist(), key=lambda item: item.filename):
            if info.is_dir():
                continue
            suffix = PurePosixPath(info.filename).suffix.lower() or "[none]"
            sha256 = _digest(archive.read(info.filename)) if info.file_size <= hash_limit_bytes else None
            entries.append(InventoryEntry(info.filename, info.file_size, suffix, sha256))
    counts = dict(sorted(Counter(item.suffix for item in entries).items()))
    return ExportInventory("zip", len(entries), sum(item.size_bytes for item in entries), counts, tuple(entries))


def write_inventory(inventory: ExportInventory, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(inventory.to_dict(), indent=2, sort_keys=True) + "\n")
