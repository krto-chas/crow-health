# ADR-0014: Descriptive statistics remain neutral and metric-scoped

## Context

Crow Health now has a normalized observation store, rebuildable index and read-only timeline. The next layer needs to summarize real observations without turning descriptive output into medical interpretation or silently combining incompatible values.

## Decision

Add a read-only descriptive statistics service above the observation timeline.

Each query targets one exact metric and may be limited by time range, evidence source and parser. Numeric integer and floating-point values are summarized with count, minimum, maximum and arithmetic mean. Boolean, text and null values are not coerced and are reported as excluded. Daily summaries use the UTC date of the recorded observation timestamp.

Observations without timestamps are excluded and counted. Multiple units for the same metric cause an explicit error instead of conversion or combination. Empty queries return an explicit empty result.

## Consequences

The platform gains deterministic machine-readable summaries suitable for later APIs and dashboards. Results preserve the current evidence and timeline boundaries and can be reproduced from the observation store.

This decision does not add trends, correlations, reference ranges, health conclusions, anomaly detection or medical advice. Unit conversion and semantic aggregation require separate evidence and decisions.
