from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class MetricValueType(StrEnum):
    INTEGER = "integer"
    NUMBER = "number"
    STRING = "string"
    BOOLEAN = "boolean"


@dataclass(frozen=True, slots=True)
class MetricDefinition:
    metric: str
    display_name: str
    description: str
    category: str
    unit: str | None
    value_type: MetricValueType
    statistics_supported: bool
    analytics_supported: bool
    deprecated: bool = False
