# ADR-0011: Full import validation

## Context

Crow Health can import individual and matching batches of Garmin JSON files, persist normalized observations and rebuild a derived index. The next milestone requires evidence from a complete local Garmin sleep import without committing personal health data or relying on manual counting.

## Decision

Add a reusable validation report over the authoritative observation store and its derived index. The report records observation and index counts, metric and parser distributions, source count, missing timestamps and observed time coverage.

Add a Garmin sleep workflow that runs the existing batch importer, rebuilds the index and produces the validation report in one command. The report may be written to a local JSON file for review, but personal source archives, observation stores and generated reports remain outside the repository.

## Consequences

- A real Garmin archive can be exercised through one deterministic command.
- Import, index and validation results are reported together.
- The validation report describes structure and counts; it does not provide medical interpretation.
- The workflow reuses existing parser, import and storage contracts.
- CI continues to use synthetic data only.
- A successful CI run verifies the workflow code, not the contents of the user's local Garmin archive.
