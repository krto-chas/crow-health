# ADR-0012: Legacy Garmin sleep compatibility

## Context

The first full local Garmin import matched 32 sleep-data files. Eleven files completed and 21 older files failed because `sleepScores` was not an object. The same report also showed isolated missing fields such as `remSleepSeconds`, `deepScore` and `interruptionsScore` in otherwise usable records.

## Decision

Keep one Garmin sleep parser and advance its parser version to 2. Core identity and timing fields remain required. Measurements and score fields that are absent in a historical schema are omitted rather than represented by invented values.

When `sleepScores` is absent or not an object, the parser emits the available non-score observations and records a structured warning. Individual missing optional measurements or score components are omitted without invalidating the complete sleep record.

## Consequences

- Historical records can preserve available sleep measurements without fabricated scores.
- Modern records continue to produce the same metrics when all fields are present.
- Observation IDs remain deterministic because they continue to use evidence ID, calendar date and metric.
- The user's local Garmin archive must be re-imported into a clean store to verify the actual historical coverage.
- This decision does not infer the undocumented meaning of legacy `sleepScores` values.
