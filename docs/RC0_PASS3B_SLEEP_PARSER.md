# RC0 Pass 3B — Garmin sleep parser

## Evidence basis

The parser contract is based on a value-free schema profile from one real Garmin sleep export member containing 99 records and 32 observed fields. Every observed field occurred in all 99 profiled records. The profile itself is private and is not committed.

## Included

- normalized `SleepSession`, `SleepStages`, `SleepRespiration`, and `SleepScore` models
- strict Garmin JSON-to-domain parsing
- conversion to existing `Observation` records
- deterministic observation identifiers
- source evidence, path, parser name, and parser version provenance
- built-in parser registry integration
- synthetic tests that reproduce only the observed structure

## Deliberate boundaries

- no database or persistence layer
- no analytics, correlations, recommendations, or medical claims
- no copied Garmin health values
- no inferred replacement values when fields are absent or malformed
- respiration units remain unset until the export semantics are independently established

A malformed record produces a structured parse error and no observations for that record. Other valid records in the same source document may still be parsed.
