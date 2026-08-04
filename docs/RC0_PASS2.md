# RC0 Pass 2 — Parser Framework

## Scope

Pass 2 introduces reusable parser infrastructure only. It does not interpret Garmin health values.

## Data flow

```text
EvidenceFile
    -> SourceDocument
    -> ParserRegistry
    -> ParserContract
    -> ParseResult
```

A parser never reads a ZIP archive directly. Archive handling, evidence preservation and document extraction remain outside parser implementations.

## Reusable contracts

- `SourceDocument` carries evidence identity, source path, media type, checksum and decoded payload.
- `ParserContract` declares supported paths and media types.
- `ParserRegistry` selects exactly one parser or returns no match.
- `ParseResult` carries records, warnings, errors and parser provenance.

## Guardrails

- Registering two parsers with the same name is rejected.
- A source document matching more than one parser is rejected as ambiguous.
- Wrong media types do not match even when the path matches.
- Parser registration does not mutate an existing registry.

## Deliberately excluded

- Sleep parsing
- HRV parsing
- Stress parsing
- Body Battery parsing
- Health analytics
- Home Assistant integration
