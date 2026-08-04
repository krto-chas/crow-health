from __future__ import annotations

import json
import re
import zipfile
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any


@dataclass(frozen=True, slots=True)
class JsonFamily:
    directory: str
    family: str
    file_count: int
    root_type: str
    observed_keys: tuple[str, ...]


def _family(name: str) -> str:
    value = re.sub(r"\d{4}-\d{2}-\d{2}_\d{4}-\d{2}-\d{2}", "<date-range>", name)
    return re.sub(r"_\d+(?=\.json$)", "_<id>", value)


def profile_json_families(path: Path, max_json_bytes: int = 10 * 1024 * 1024) -> tuple[JsonFamily, ...]:
    groups: dict[tuple[str, str], list[zipfile.ZipInfo]] = defaultdict(list)
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            if info.is_dir() or not info.filename.lower().endswith(".json"):
                continue
            pure = PurePosixPath(info.filename)
            groups[(str(pure.parent), _family(pure.name))].append(info)
        result: list[JsonFamily] = []
        for (directory, family), infos in sorted(groups.items()):
            keys: set[str] = set()
            root_types: set[str] = set()
            for info in infos:
                if info.file_size > max_json_bytes:
                    root_types.add("skipped-large-json")
                    continue
                value: Any = json.loads(archive.read(info.filename))
                if isinstance(value, dict):
                    root_types.add("object")
                    keys.update(str(key) for key in value)
                elif isinstance(value, list):
                    root_types.add("array")
                    for item in value[:20]:
                        if isinstance(item, dict):
                            keys.update(str(key) for key in item)
                else:
                    root_types.add(type(value).__name__)
            result.append(JsonFamily(directory, family, len(infos), "+".join(sorted(root_types)), tuple(sorted(keys))))
    return tuple(result)


def write_profile(families: tuple[JsonFamily, ...], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps([asdict(item) for item in families], indent=2, sort_keys=True) + "\n")
