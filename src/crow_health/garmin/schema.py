from __future__ import annotations

import json
import zipfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class JsonFieldProfile:
    path: str
    observed_types: tuple[str, ...]
    occurrences: int
    missing_from_records: int

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "observed_types": list(self.observed_types),
            "occurrences": self.occurrences,
            "missing_from_records": self.missing_from_records,
        }


@dataclass(frozen=True, slots=True)
class JsonSchemaProfile:
    source_path: str
    root_type: str
    record_count: int
    fields: tuple[JsonFieldProfile, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "source_path": self.source_path,
            "root_type": self.root_type,
            "record_count": self.record_count,
            "fields": [field.to_dict() for field in self.fields],
        }


def _type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def _walk(value: Any, path: str, types: dict[str, Counter[str]], seen: set[str]) -> None:
    types.setdefault(path, Counter())[_type_name(value)] += 1
    seen.add(path)

    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else key
            _walk(child, child_path, types, seen)
    elif isinstance(value, list):
        item_path = f"{path}[]"
        for child in value:
            _walk(child, item_path, types, seen)


def profile_json_payload(source_path: str, payload: Any) -> JsonSchemaProfile:
    records = payload if isinstance(payload, list) else [payload]
    record_count = len(records)
    types: dict[str, Counter[str]] = {}
    presence: Counter[str] = Counter()

    for record in records:
        seen: set[str] = set()
        _walk(record, "$", types, seen)
        presence.update(seen)

    fields = tuple(
        JsonFieldProfile(
            path=path,
            observed_types=tuple(sorted(type_counts)),
            occurrences=sum(type_counts.values()),
            missing_from_records=max(0, record_count - presence[path]),
        )
        for path, type_counts in sorted(types.items())
    )
    return JsonSchemaProfile(
        source_path=source_path,
        root_type=_type_name(payload),
        record_count=record_count,
        fields=fields,
    )


def inspect_zip_json(archive: Path, member_path: str) -> JsonSchemaProfile:
    with zipfile.ZipFile(archive) as zf:
        try:
            raw = zf.read(member_path)
        except KeyError as exc:
            raise ValueError(f"JSON member not found in archive: {member_path}") from exc
    payload = json.loads(raw.decode("utf-8-sig"))
    return profile_json_payload(member_path, payload)


def write_schema_profile(profile: JsonSchemaProfile, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(profile.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
