# ADR-0024: Authenticated Apple Health manifest intake

## Context

The physical-device collector can generate a value-free Apple Health coverage manifest, but Crow Health needs a controlled way to receive and preserve that evidence before sample-value ingestion is designed.

## Decision

Add one authenticated HTTP endpoint for the versioned manifest contract. Authentication uses an operator-provided bearer token. Accepted payloads are strictly validated, canonicalized, SHA-256 identified and archived immutably. Repeated identical uploads are idempotent.

## Consequences

This creates an end-to-end path for coverage evidence without introducing health sample values. The bearer token must be delivered only over TLS in deployment and must not be committed. This endpoint does not authorize sample ingestion, background delivery, observation creation or production use on an untrusted network.
