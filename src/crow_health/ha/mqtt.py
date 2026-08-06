from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from crow_health.snapshot import PresentationSnapshot, SnapshotMetric


@dataclass(frozen=True, slots=True)
class HaMqttMessage:
    topic: str
    payload: str
    retain: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {"topic": self.topic, "payload": self.payload, "retain": self.retain}


class HomeAssistantMqttAdapter:
    """Project a verified snapshot into Home Assistant MQTT discovery messages."""

    def __init__(
        self,
        *,
        discovery_prefix: str = "homeassistant",
        state_prefix: str = "crow-health",
        device_id: str = "crow_health",
    ) -> None:
        self._discovery_prefix = discovery_prefix.strip("/")
        self._state_prefix = state_prefix.strip("/")
        self._device_id = _slug(device_id)

    def messages(self, snapshot: PresentationSnapshot) -> tuple[HaMqttMessage, ...]:
        messages: list[HaMqttMessage] = []
        for metric in snapshot.metrics:
            messages.extend(self._metric_messages(metric))
        return tuple(messages)

    def _metric_messages(self, metric: SnapshotMetric) -> tuple[HaMqttMessage, HaMqttMessage]:
        object_id = _slug(metric.metric)
        state_topic = f"{self._state_prefix}/{self._device_id}/{object_id}/state"
        config_topic = (
            f"{self._discovery_prefix}/sensor/{self._device_id}/{object_id}/config"
        )
        config: dict[str, Any] = {
            "name": metric.display_name,
            "unique_id": f"{self._device_id}_{object_id}",
            "object_id": f"{self._device_id}_{object_id}",
            "state_topic": state_topic,
            "value_template": "{{ value_json.value }}",
            "json_attributes_topic": state_topic,
            "device": {
                "identifiers": [self._device_id],
                "name": "Crow Health",
                "manufacturer": "Crow",
                "model": "Health RC0",
            },
        }
        if metric.unit is not None:
            config["unit_of_measurement"] = metric.unit

        state = {
            "value": metric.latest_value,
            "metric": metric.metric,
            "description": metric.description,
            "category": metric.category,
            "value_type": metric.value_type,
            "latest_day": metric.latest_day,
            "moving_average": metric.moving_average,
            "trend_direction": metric.trend_direction,
            "coverage_percent": metric.coverage_percent,
            "observation_count": metric.observation_count,
            "schema_version": snapshot_schema(metric),
        }
        return (
            HaMqttMessage(config_topic, json.dumps(config, sort_keys=True)),
            HaMqttMessage(state_topic, json.dumps(state, sort_keys=True, default=str)),
        )


def snapshot_schema(metric: SnapshotMetric) -> str:
    """Return the projection schema without inferring from metric values."""
    del metric
    return "crow-health.ha-mqtt.v1"


def _slug(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    if not normalized:
        raise ValueError("Identifier must contain at least one alphanumeric character")
    return normalized
