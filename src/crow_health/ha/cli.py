from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from crow_health.analytics import AnalyticsService
from crow_health.ha.mqtt import HomeAssistantMqttAdapter
from crow_health.snapshot import SnapshotQuery, SnapshotService
from crow_health.statistics import DescriptiveStatistics
from crow_health.storage import JsonlObservationIndex
from crow_health.timeline import ObservationTimeline


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="crow-health-ha")
    root.add_argument("--metric", action="append", required=True)
    root.add_argument("--store", type=Path, default=Path("data/observations.jsonl"))
    root.add_argument("--index", type=Path, default=None)
    root.add_argument("--from", dest="observed_from", type=datetime.fromisoformat)
    root.add_argument("--to", dest="observed_to", type=datetime.fromisoformat)
    root.add_argument("--window-days", type=int, default=7)
    root.add_argument("--discovery-prefix", default="homeassistant")
    root.add_argument("--state-prefix", default="crow-health")
    root.add_argument("--device-id", default="crow_health")
    root.add_argument("--output", type=Path, default=None)
    return root


def main() -> int:
    args = parser().parse_args()
    statistics = DescriptiveStatistics(
        ObservationTimeline(JsonlObservationIndex(args.store, args.index))
    )
    snapshot = SnapshotService(statistics, AnalyticsService(statistics)).build(
        SnapshotQuery(
            metrics=tuple(args.metric),
            observed_from=args.observed_from,
            observed_to=args.observed_to,
            moving_average_window_days=args.window_days,
        )
    )
    messages = HomeAssistantMqttAdapter(
        discovery_prefix=args.discovery_prefix,
        state_prefix=args.state_prefix,
        device_id=args.device_id,
    ).messages(snapshot)
    payload = "\n".join(json.dumps(message.to_dict(), sort_keys=True) for message in messages)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(f"{payload}\n", encoding="utf-8")
    print(payload)
    return 0
