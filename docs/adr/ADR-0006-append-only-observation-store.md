# ADR-0006: Append-only observation store

## Status

Proposed in RC0 Pass 4.

## Context

Parsers now produce deterministic `Observation` records with source and parser provenance. RC0 needs a local persistence boundary before additional data types or analytics are added.

A production database would introduce schema migration, deployment and operational decisions before the observation contract has been exercised. At the same time, writing arbitrary JSON files would weaken duplicate detection and traceability.

## Decision

Introduce an `ObservationStore` protocol and a local JSON Lines implementation.

The store is append-only:

- a new observation ID is appended;
- an identical repeated observation is treated as an idempotent existing record;
- the same observation ID with different content is rejected as a conflict;
- existing duplicate IDs are treated as store corruption;
- no update or delete operation is exposed.

JSON Lines is an RC0 persistence adapter, not the permanent database decision. Domain and parser code depend on the storage contract, not the file format.

## Consequences

The parser output can be persisted and replayed without selecting PostgreSQL or another database prematurely. The implementation remains inspectable and portable across Windows and Linux.

The adapter performs a full scan and is not intended for large-scale querying. Indexes, transactions across processes, migrations and concurrent writers are deferred to a later persistence pass.
