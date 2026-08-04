# Changelog

## Unreleased — RC0 Pass 3B

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
