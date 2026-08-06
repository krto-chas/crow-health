# ADR-0020: Home Assistant MQTT adapter

## Context

Crow Health now exposes verified, versioned snapshots and a read-only HTTP API. Home Assistant should consume those derived values without duplicating parser, storage, statistics or analytics logic.

The current Garmin ingestion path is archive based. No verified automatic Garmin retrieval mechanism exists in the project.

## Decision

Add a thin adapter that projects `PresentationSnapshot` metrics into deterministic Home Assistant MQTT discovery and state messages.

The adapter:

- emits retained discovery and state messages;
- derives entity identity from registered metric identifiers;
- includes snapshot-derived attributes such as moving average, trend and coverage;
- performs no health calculation and assigns no medical meaning;
- exposes a separate `crow-health-ha` export command that writes JSON Lines messages suitable for review or a later publisher.

The adapter does not connect to a broker in this pass. Broker credentials, retries, scheduling and deployment are separate operational concerns.

## Consequences

Home Assistant entity configuration can be generated from the same verified snapshot contract used by the API. The output remains inspectable and deterministic before network publication.

Pass 18 does not make Garmin data current automatically. Until a separately verified live Garmin source adapter exists, Home Assistant will only reflect observations already imported into Crow Health.
