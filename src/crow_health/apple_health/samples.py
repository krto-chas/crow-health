from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

APPLE_HEALTH_SAMPLE_SCHEMA = "crow-health.apple-health-samples.v1"
SUPPORTED_IDENTIFIERS = frozenset(
    {
        "HKCategoryTypeIdentifierSleepAnalysis",
        "HKQuantityTypeIdentifierHeartRate",
        "HKQuantityTypeIdentifierRestingHeartRate",
        "HKQuantityTypeIdentifierStepCount",
        "HKQuantityTypeIdentifierActiveEnergyBurned",
        "HKQuantityTypeIdentifierBodyMass",
    }
)


class AppleHealthSampleKind(StrEnum):
    QUANTITY = "quantity"
    CATEGORY = "category"


@dataclass(frozen=True, slots=True)
class AppleHealthSample:
    sample_id: str
    identifier: str
    kind: AppleHealthSampleKind
    source_bundle_id: str
    source_name: str
    start_at: datetime
    end_at: datetime
    value: float | int | str
    unit: str | None


@dataclass(frozen=True, slots=True)
class AppleHealthSampleBatch:
    schema_version: str
    collector_id: str
    generated_at: datetime
    anchor: str | None
    samples: tuple[AppleHealthSample, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def evidence_id(self) -> str:
        canonical = json.dumps(
            self.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()


def load_sample_batch(payload: object) -> AppleHealthSampleBatch:
    if not isinstance(payload, dict):
        raise TypeError("Apple Health sample batch must be an object")
    if payload.get("schema_version") != APPLE_HEALTH_SAMPLE_SCHEMA:
        raise ValueError("Unsupported Apple Health sample schema")

    collector_id = _string(payload, "collector_id")
    generated_at = _datetime(payload, "generated_at")
    anchor = _optional_string(payload, "anchor")
    raw_samples = payload.get("samples")
    if not isinstance(raw_samples, list):
        raise TypeError("samples must be an array")

    samples = tuple(_sample(item) for item in raw_samples)
    sample_ids = [item.sample_id for item in samples]
    if len(sample_ids) != len(set(sample_ids)):
        raise ValueError("sample_id values must be unique within a batch")

    return AppleHealthSampleBatch(
        schema_version=APPLE_HEALTH_SAMPLE_SCHEMA,
        collector_id=collector_id,
        generated_at=generated_at,
        anchor=anchor,
        samples=tuple(sorted(samples, key=lambda item: (item.start_at, item.sample_id))),
    )


def _sample(raw: object) -> AppleHealthSample:
    if not isinstance(raw, dict):
        raise TypeError("sample must be an object")
    identifier = _string(raw, "identifier")
    if identifier not in SUPPORTED_IDENTIFIERS:
        raise ValueError(f"Unsupported HealthKit identifier: {identifier}")

    kind = AppleHealthSampleKind(_string(raw, "kind"))
    start_at = _datetime(raw, "start_at")
    end_at = _datetime(raw, "end_at")
    if end_at < start_at:
        raise ValueError("end_at must not be earlier than start_at")

    value = raw.get("value")
    unit = _optional_string(raw, "unit")
    if kind is AppleHealthSampleKind.QUANTITY:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError("quantity sample value must be numeric")
        if unit is None:
            raise ValueError("quantity sample unit is required")
    else:
        if not isinstance(value, (int, str)) or isinstance(value, bool):
            raise TypeError("category sample value must be an integer or string")
        if unit is not None:
            raise ValueError("category sample unit must be null")

    return AppleHealthSample(
        sample_id=_string(raw, "sample_id"),
        identifier=identifier,
        kind=kind,
        source_bundle_id=_string(raw, "source_bundle_id"),
        source_name=_string(raw, "source_name"),
        start_at=start_at,
        end_at=end_at,
        value=value,
        unit=unit,
    )


def _string(raw: dict[str, Any], field: str) -> str:
    value = raw.get(field)
    if not isinstance(value, str) or not value.strip():
        raise TypeError(f"{field} must be a non-empty string")
    return value


def _optional_string(raw: dict[str, Any], field: str) -> str | None:
    value = raw.get(field)
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string or null")
    return value


def _datetime(raw: dict[str, Any], field: str) -> datetime:
    value = _string(raw, field)
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must include a timezone offset")
    return parsed
