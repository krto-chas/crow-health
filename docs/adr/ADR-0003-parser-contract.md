# ADR-0003: Parser contract

## Decision
Each source parser declares name, version and supported path patterns and emits only normalized Observation objects.

## Consequences
Garmin-specific fields remain outside the core model. Parser implementations are deferred until observed schemas are reviewed.
