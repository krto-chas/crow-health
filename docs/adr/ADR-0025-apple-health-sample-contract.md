# ADR-0025: Version Apple Health sample batches before ingestion

## Context

The physical-device collector and value-free manifest establish which HealthKit types and sources are available. The next step requires a contract for actual sample values, but the verified Crow Health observation pipeline must not be changed before source behavior, units and identifiers have been reviewed on a physical device.

## Decision

Introduce `crow-health.apple-health-samples.v1` as a strict source contract for the six HealthKit identifiers already reviewed in RC1 Pass 2.

Each sample preserves:

- HealthKit sample identifier
- HealthKit type identifier
- quantity or category kind
- source name and bundle identifier
- timezone-aware start and end timestamps
- original value and unit

Each batch also preserves a collector identifier, generation time and opaque HealthKit anchor. Canonical JSON produces a deterministic SHA-256 evidence identity.

Unknown identifiers, duplicate sample identifiers, naive timestamps, invalid ranges, missing quantity units and incompatible value kinds fail closed.

## Consequences

The iOS collector and server can now target one versioned contract without assuming Crow Health metric mappings. Raw sample batches can later be archived immutably and processed idempotently.

This decision does not authorize upload, background delivery, normalization, metric-registry expansion or observation persistence. Those remain separate passes and require physical-device evidence from the collector.
