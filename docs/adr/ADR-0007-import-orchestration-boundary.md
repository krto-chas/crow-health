# ADR-0007: Import orchestration boundary

## Status

Proposed in RC0 Pass 5.

## Context

Crow Health now has separate source-document, parser, observation and persistence contracts. Without an orchestration boundary, CLI commands or future APIs would need to duplicate parser selection, error handling and storage behavior.

Parsers must remain independent of ZIP archives and persistence adapters. The observation store must not know how source files are decoded or parsed.

## Decision

Introduce an `ImportService` that coordinates one `SourceDocument` through the parser registry and into an `ObservationStore`.

The service:

- selects exactly one parser through the existing registry;
- reports a structured error when no parser matches;
- persists no observations when parsing reports any error;
- appends successful parser output through the storage contract;
- returns counts for parsed, inserted and already-existing observations.

Source adapters remain separate. RC0 includes a ZIP JSON-member adapter that reads an exact archive member, calculates its SHA-256 checksum and creates a `SourceDocument`. Parsers continue to receive only `SourceDocument` instances.

## Consequences

CLI, API and future background jobs can reuse one deterministic import path. Source decoding, parsing and storage remain independently replaceable and testable.

The service currently imports one source document at a time. Batch planning, resumable jobs, concurrent imports and production transactions are deferred.
