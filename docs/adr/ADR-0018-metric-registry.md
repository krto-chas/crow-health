# ADR-0018: Normalized metric registry

## Context

Normalized observations currently identify metrics with strings. Parsers, snapshots and future integrations need one authoritative definition for display metadata, units, value types and supported derived operations. Repeating that metadata in each consumer would create drift.

## Decision

Introduce an immutable in-process `MetricRegistry` containing explicit `MetricDefinition` records. The initial registry covers every metric emitted by the Garmin sleep parser.

The registry:

- rejects duplicate definitions;
- fails closed for unknown metric lookup;
- provides deterministic category and exact-metric filtering;
- validates observation unit and value type when explicitly invoked;
- enriches presentation snapshots with display name, description, category and value type.

Definitions describe normalized Crow Health metrics, not Garmin source fields. Text and boolean metrics explicitly declare that numeric statistics and analytics are unsupported.

## Consequences

Dashboard and integration layers can consume shared metadata instead of maintaining private naming tables. Adding a parser metric now requires adding a corresponding registry definition. Snapshot requests for unknown metrics fail instead of returning invented metadata.

This pass does not add automatic validation to the persistence pipeline, metric aliases, translations, medical interpretation or external configuration loading.
