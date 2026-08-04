# ADR-0002: Immutable raw data

## Decision
Original exports are copied into a content-addressed raw evidence directory and never modified in place.

## Consequences
Repeated imports are idempotent. Storage use increases, but provenance is retained.
