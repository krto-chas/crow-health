# ADR-0015: Observation catalog

## Status

Accepted for RC0 Pass 13.

## Context

Crow Health can import, index, validate, query and summarize normalized observations. As additional parsers and sources are added, consumers need a deterministic way to discover which metrics actually exist in the authoritative store and what structural properties those observations have.

A hard-coded list would drift from stored evidence and would couple future interfaces to Garmin-specific assumptions.

## Decision

Add a read-only `ObservationCatalog` that scans the authoritative observation store and groups observations by exact metric name.

For each metric, report only properties demonstrated by stored observations:

- observation and timestamp counts;
- first and last observation timestamps;
- covered UTC dates;
- observed value types and units;
- contributing parsers and evidence-source count;
- numeric observation count;
- whether the existing descriptive statistics service can safely operate without coercion or unit conversion.

Catalog output is deterministic and can be filtered by metric prefix, parser or source evidence ID.

## Consequences

The platform gains a source-independent discovery layer for future APIs, dashboards and Home Assistant entities. New parsers automatically extend the catalog through their normalized observations.

The catalog does not define canonical display names, medical semantics, reference ranges or unit conversions. It reports what is present; it does not reinterpret or repair stored data.
