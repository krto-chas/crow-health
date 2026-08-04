# Changelog

## Unreleased — RC0 Pass 6

- Added deterministic discovery of matching JSON members inside ZIP archives.
- Added reusable batch import orchestration built on the existing single-document pipeline.
- Added per-member and aggregate reports for parsed, inserted, existing and failed records.
- Added failure isolation so one malformed member does not prevent later members from being processed.
- Added the `import-json-batch` CLI command with repeatable glob patterns.
- Added tests for sorting, filtering, idempotency, partial failure and empty matches.
- No scheduler, resumable job state, concurrency, analytics, API or Home Assistant integration has been added.

## RC0 Pass 5

- Added a reusable import orchestration service between source adapters, parser registry and observation storage.
- Added exact ZIP JSON-member loading with SHA-256 source identity.
- Added fail-closed persistence when a parser reports errors.
- Added structured import reports with parsed, inserted and existing record counts.
- Added the `import-json-member` CLI command.
- Added tests for successful import, idempotency, parser failures, missing parsers and deterministic source loading.
- No batch scheduler, API, analytics or Home Assistant integration has been added.

## RC0 Pass 4

- Added the reusable `ObservationStore` contract.
- Added an append-only JSON Lines storage adapter for normalized observations.
- Added idempotent repeated imports and explicit conflict detection for reused observation IDs.
- Added corruption detection for duplicate IDs already present in the store.
- Added round-trip, conflict, atomicity and invalid-data tests.
- No production database, analytics, API or Home Assistant integration has been added.

## RC0 Pass 3B

- Added normalized `SleepSession`, `SleepStages`, `SleepRespiration` and `SleepScore` models.
- Added strict Garmin sleep parsing based on a value-free profile of 99 real export records and 32 observed fields.
- Added deterministic observation identifiers and full source/parser provenance.
- Added built-in parser registry integration.
- Added synthetic tests for valid data, deterministic IDs, malformed records and registry matching.
- No database, analytics, Home Assistant integration or medical interpretation has been added.

## RC0 Pass 3A

- Added value-free JSON schema inspection for exact Garmin ZIP members.
- Added field occurrence, missing-field and observed-type reporting.
- Added the `inspect-json` CLI command.

## RC0 Pass 2

- Added reusable `SourceDocument`, `ParseMessage` and `ParseResult` models.
- Refined `ParserContract` to operate on source documents and return traceable results.
- Added immutable `ParserRegistry` with path and media-type matching.
- Added duplicate-registration and ambiguous-match protection.
- Added parser-registry tests.
- Added GitHub Actions quality gates for Python 3.11 and 3.13 on Linux and Windows.
- No health-data parser logic has been added in this pass.

## 0.3.0 — RC0 Pass 1

- Added immutable evidence archive and evidence models.
- Added deterministic Garmin ZIP inventory.
- Added structural JSON-family profiler without extracting personal values.
- Added parser protocol and initial parser contracts.
- Added tests for archive, inventory, profiling and missing-value preservation.
- Removed dashboard, MQTT, API and analytics from RC0 scope.
