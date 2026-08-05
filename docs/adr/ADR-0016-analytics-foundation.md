# ADR-0016: Deterministic analytics foundation

## Context

Crow Health can import, index, catalog and summarize normalized observations. Dashboard and automation consumers need reusable calculations, but medical interpretation and source-specific logic remain outside RC0.

## Decision

Add a read-only analytics service above descriptive statistics. The first supported calculations are calendar-window moving averages, first-to-last trend, daily completeness and IQR outlier detection.

Calculations operate on exact metrics and daily numeric means. Missing days are not filled, values are not coerced, units are not converted and statistical outliers are not assigned medical meaning.

## Consequences

The same calculations can be reused for Garmin and future normalized sources. Results remain deterministic and traceable to stored observations. More advanced trend models, correlations, medical thresholds, dashboards and Home Assistant integration remain separate future decisions.
