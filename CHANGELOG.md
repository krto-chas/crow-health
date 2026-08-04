# Changelog

## Unreleased — RC0 Pass 2

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
