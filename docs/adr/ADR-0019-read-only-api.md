# ADR-0019: Read-only HTTP API

## Context

Crow Health now has verified services for the metric registry, observation catalog, timeline, descriptive statistics and versioned presentation snapshots. Dashboard and Home Assistant clients need a stable transport boundary without duplicating domain or analytics logic.

## Decision

Expose a versioned FastAPI application that delegates directly to the existing read services.

The API provides:

- runtime health and identity;
- metric registry lookup;
- observation catalog queries;
- timeline queries;
- exact-metric descriptive statistics;
- multi-metric presentation snapshots.

The authoritative observation store remains append-only and the API exposes no mutation endpoints. Store and index paths are supplied explicitly to the application factory or through environment variables. Unknown registered metrics fail with HTTP 404 rather than producing inferred metadata.

## Consequences

Dashboard, Home Assistant and other clients can consume one stable JSON interface while sharing the same calculations and registry contracts as the CLI. HTTP serialization and parameter validation are isolated from the domain services.

This pass does not add authentication, TLS termination, CORS policy, scheduling, import endpoints, deployment manifests or write operations. Those concerns require separate decisions before the API is exposed outside a trusted network.
