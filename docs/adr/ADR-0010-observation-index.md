# ADR-0010: Rebuildable observation index

## Context

The append-only JSONL observation store is intentionally simple and auditable, but its existing `all()` and `get()` operations scan the complete file. Historical Garmin imports and future Apple Health or Oura sources will increase the number of observations substantially. Query and analysis features should not require rewriting the source store or loading every observation for each request.

## Decision

Add a separate, rebuildable JSONL index containing only observation metadata and byte locations in the source store.

Each index entry records:

- observation ID
- metric
- source evidence ID and source path
- parser name
- observation timestamp
- byte offset and byte length in the source JSONL file

The index is derived data, not evidence. It may be deleted and rebuilt from the append-only observation store. Rebuilds are written to a temporary file and replace the previous index only after the complete store has been read successfully.

Queries filter index metadata first and then seek directly to matching observation records. A mismatch between an index entry and the current store is rejected as a stale or invalid index.

## Consequences

- Existing parsers, observations and JSONL storage remain unchanged.
- Metric, source, parser and time-range queries avoid deserializing unrelated observations.
- Corrupt source data cannot partially replace a previously valid index.
- Appending new observations makes an existing index incomplete until it is rebuilt.
- The index is not authoritative and must never be treated as the only copy of health data.
- Incremental index maintenance and automatic rebuild scheduling remain outside RC0 Pass 8.
