# ADR-0017: Versioned presentation snapshots

## Context

Crow Health now exposes observations, timelines, descriptive statistics, a metric catalog and deterministic analytics. A dashboard or Home Assistant integration should not need to reproduce those calculations or depend directly on the append-only observation format.

## Decision

Introduce a read-only presentation snapshot service with an explicit schema version.

A snapshot is built from an explicit list of exact metrics and optional time, parser and evidence-source filters. Each metric entry contains compact descriptive statistics, the latest daily value, the latest calendar-window moving average, first-to-last trend, completeness and IQR outlier count.

Metric names are de-duplicated and sorted. Missing metrics remain explicit empty entries. The snapshot contains no generation timestamp so identical stored evidence and identical query parameters produce identical output.

The `snapshot-export` CLI command can print the JSON payload or write it to a selected file. The snapshot is a derived read model and never replaces the authoritative observation store.

## Consequences

Dashboard, Home Assistant and other consumers can depend on one small versioned JSON contract rather than internal storage and analytics classes.

Schema changes require a new schema version. The service does not assign medical meaning, fill missing days, convert units, select metrics automatically or transport data to Home Assistant. Scheduling, HTTP APIs and MQTT remain separate future concerns.
