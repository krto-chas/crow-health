# Changelog

## Unreleased — RC0 Pass 15

- Added a versioned, deterministic presentation snapshot contract.
- Added compact per-metric statistics, latest values, moving averages, trends, coverage and outlier counts.
- Added multi-metric `snapshot-export` CLI output with optional JSON file writing.
- Added source, parser and explicit time-range filtering.
- Added synthetic tests for deterministic ordering, empty metrics and invalid windows.
- No dashboard, Home Assistant transport, medical interpretation or generated personal snapshot has been committed.

## RC0 Pass 14

- Added deterministic analytics over exact numeric metrics.
- Added calendar-window moving averages, first-to-last trends and daily completeness.
- Added IQR-based statistical outlier identification without medical interpretation.
- Added the `analytics` CLI command and synthetic tests.
- No prediction, AI, correlation analysis, dashboard or Home Assistant integration has been added.

## RC0 Pass 13

- Added a deterministic observation catalog over the authoritative store.
- Added per-metric counts, timestamp coverage, value types, units, parsers and source counts.
- Added explicit numeric counts and statistics-support reporting without coercion or unit conversion.
- Added metric-prefix, parser and source filtering.
- Added the `catalog` CLI command and runtime capability reporting.
- Added synthetic tests for ordering, filtering, mixed units, non-numeric values and empty stores.
- No medical interpretation, metric naming registry, dashboard or Home Assistant integration has been added.

## RC0 Pass 12

- Added neutral descriptive statistics for one exact numeric metric at a time.
- Added count, minimum, maximum, arithmetic mean and timestamp coverage.
- Added deterministic UTC daily summaries and covered-day counts.
- Added explicit exclusion counts for non-numeric and timestamp-free observations.
- Added mixed-unit rejection instead of combining incompatible values.
- Added the `statistics` CLI command and runtime capability reporting.
- Added synthetic tests for numeric summaries, daily grouping, ranges and invalid units.
- No medical interpretation, trend inference, correlation, dashboard or Home Assistant integration has been added.

## RC0 Pass 11

- Added a read-only observation timeline over the rebuildable index.
- Added deterministic grouping by observation timestamp, evidence source and parser.
- Added UTC day, explicit time range, source, parser and metric-prefix filtering.
- Added reporting for observations excluded because they lack timestamps.
- Added the `timeline-query` CLI command and runtime capability reporting.
- Added synthetic tests for grouping, ordering, filtering and missing timestamps.
- No analytics, medical interpretation, dashboard or Home Assistant integration has been added.

## RC0 Pass 10

- Added legacy-compatible Garmin sleep parsing based on the first full local archive report.
- Preserved available measurements when `sleepScores` is absent or not an object.
- Made historically variable measurements and individual score components optional.
- Omitted unavailable metrics instead of creating guessed or placeholder values.
- Added structured warnings for legacy records without score objects.
- Added synthetic tests for legacy records and partially populated modern records.
- No undocumented legacy score interpretation or personal Garmin data has been committed.

## RC0 Pass 9

- Added a full Garmin sleep import workflow that runs batch import, index rebuild and validation.
- Added deterministic validation summaries for observations, metrics, parsers, sources and time coverage.
- Added `garmin-sleep-import` and `validate-store` CLI commands.
- Added optional JSON report output for evidence from a real local Garmin archive run.
- Added tests for populated and empty stores.
- No personal Garmin data or generated validation report has been committed.

## RC0 Pass 8

- Added a rebuildable metadata index for append-only JSONL observations.
- Added byte-offset lookup without changing the authoritative observation store.
- Added metric, source evidence, parser and observation-time filtering.
- Added atomic index replacement and stale-index mismatch detection.
- Added the `index-build` and `index-query` CLI commands.
- Added tests for rebuilding, filtering, idempotency, empty stores and corruption.
- No incremental index updater, scheduler, analytics, API or Home Assistant integration has been added.

## RC0 Pass 7

- Added the `crow-health version` runtime identity command.
- Added installed package, Python, platform, executable and project-root reporting.
- Added Git commit detection with an explicit deployment override.
- Added a machine-readable capability list for CLI verification.
- Added cross-platform tests and ADR-0009.
- No health-data reading, analytics, API or Home Assistant integration has been added.

## RC0 Pass 6

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
