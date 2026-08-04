# ADR-0008: Deterministic batch import

## Status

Proposed in RC0 Pass 6.

## Context

The single-document import pipeline can parse and persist one exact source member. A Garmin export contains many time-sliced files of the same family, so manual invocation for every member is error-prone and does not produce one aggregate result.

Batch behavior must reuse the existing source, parser and storage boundaries rather than introducing a second import path.

## Decision

Add a batch service that discovers ZIP members from explicit glob patterns, sorts them deterministically and sends each member through the existing `load_json_zip_member` and `ImportService` path.

Each member receives its own report. A failed source or parser result is recorded and does not stop later members. Successful members retain the existing append-only and idempotent storage semantics.

An empty match is not considered a successful batch. RC0 provides no concurrency, scheduler or resumable job state.

## Consequences

All historical Garmin sleep files can be imported with one command while preserving exact per-file provenance and parser behavior. Repeated batch imports remain idempotent through deterministic observation identifiers and the existing store contract.

The batch is not atomic across all members. A later failure can coexist with observations persisted from earlier successful members, and the report must be retained as the evidence of that outcome. Resumable jobs and production transaction boundaries remain deferred.
