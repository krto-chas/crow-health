from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from crow_health.apple_health.models import AppleHealthManifestEntry


def load_manifest(path: Path) -> tuple[AppleHealthManifestEntry, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return load_manifest_payload(payload)


def load_manifest_payload(payload: object) -> tuple[AppleHealthManifestEntry, ...]:
    if not isinstance(payload, dict) or payload.get("schema_version") != "crow-health.apple-health-manifest.v1":
        raise ValueError("Unsupported Apple Health manifest schema")
    raw_entries = payload.get("entries")
    if not isinstance(raw_entries, list):
        raise TypeError("entries must be an array")
    return tuple(_entry(item) for item in raw_entries)


def _entry(raw: object) -> AppleHealthManifestEntry:
    if not isinstance(raw, dict):
        raise TypeError("manifest entry must be an object")
    return AppleHealthManifestEntry(
        identifier=_string(raw, "identifier"),
        source_bundle_id=_string(raw, "source_bundle_id"),
        source_name=_string(raw, "source_name"),
        sample_count=_integer(raw, "sample_count"),
        earliest_sample=_optional_string(raw, "earliest_sample"),
        latest_sample=_optional_string(raw, "latest_sample"),
        observed_units=_strings(raw, "observed_units"),
    )


def _string(raw: dict[str, Any], field: str) -> str:
    value = raw.get(field)
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    return value


def _optional_string(raw: dict[str, Any], field: str) -> str | None:
    value = raw.get(field)
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string or null")
    return value


def _integer(raw: dict[str, Any], field: str) -> int:
    value = raw.get(field)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise TypeError(f"{field} must be a non-negative integer")
    return value


def _strings(raw: dict[str, Any], field: str) -> tuple[str, ...]:
    value = raw.get(field)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise TypeError(f"{field} must be an array of strings")
    return tuple(sorted(set(value)))
