# ADR-0005: Normalize sleep data before observation storage

## Context

The observed Garmin sleep export groups session timing, sleep stages, respiration, and sleep scores in one vendor-specific JSON object. Persisting that object directly would couple Crow Health to Garmin field names and nesting.

## Decision

The Garmin parser first creates vendor-neutral `SleepSession`, `SleepStages`, `SleepRespiration`, and `SleepScore` models. It then emits the existing provenance-bearing `Observation` model.

The parser is strict: missing fields, invalid types, or invalid date/timestamp strings produce a parse error. It does not guess, interpolate, or substitute values.

## Consequences

- future sources can map into the same sleep domain models
- Garmin schema changes remain isolated in the Garmin parser
- source provenance remains attached to every emitted observation
- the initial parser supports only the schema actually observed in the profiled export
