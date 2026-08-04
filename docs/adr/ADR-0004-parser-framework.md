# ADR-0004: Shared parser framework

## Context

Crow Health will receive data from multiple vendors and export formats. Repeating provenance, matching and error-handling logic in every parser would create drift and make later sources harder to add.

## Decision

All parsers implement one `ParserContract`, receive a `SourceDocument` and return a `ParseResult`. Parser selection is handled by an immutable `ParserRegistry` using explicit path patterns and media types.

Parsers do not read ZIP archives or perform evidence archiving. They only transform one already-decoded source document into normalised records and parse messages.

## Consequences

- Common provenance and result handling can be reused across vendors.
- Ambiguous parser matches fail explicitly.
- Vendor-specific code remains small and visible.
- Archive extraction must remain a separate pipeline step.
