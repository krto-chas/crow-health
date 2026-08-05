# ADR-0013: Read-only observation timeline

## Context

The observation store and rebuildable index provide durable storage and efficient lookup, but consumers still need a deterministic way to view observations in chronological groups. Future analytics, dashboards and integrations should not each invent their own grouping and ordering rules.

## Decision

Add a read-only timeline service above the observation index.

Timeline groups are formed from observations that share:

- observation timestamp
- source evidence ID
- parser name

Groups and observations within each group are sorted deterministically. Queries may constrain UTC day, explicit time range, source evidence ID, parser name and metric prefix. Observations without a timestamp are not assigned an invented time; they are excluded and counted in the result.

The timeline does not write to the observation store or index and is not authoritative evidence.

## Consequences

- Consumers receive one common chronological representation.
- Multiple metrics from the same imported sleep session remain together.
- Identical timestamps from different evidence sources remain separate.
- Missing timestamps remain explicit rather than being guessed.
- UTC day filtering is deterministic across operating systems.
- Analytics, aggregation, visualization and medical interpretation remain outside this decision.
