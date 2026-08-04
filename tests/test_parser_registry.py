from __future__ import annotations

from dataclasses import dataclass

import pytest

from crow_health.parsers.models import ParseResult, SourceDocument
from crow_health.parsers.registry import ParserRegistry


@dataclass(frozen=True, slots=True)
class FakeParser:
    name: str
    version: str = "1.0.0"
    supported_path_patterns: tuple[str, ...] = ("*/sleepData.json",)
    supported_media_types: tuple[str, ...] = ("application/json",)

    def parse(self, document: SourceDocument) -> ParseResult:
        return ParseResult.success(
            records=(),
            parser_name=self.name,
            parser_version=self.version,
            source_evidence_id=document.evidence_id,
        )


def source_document(
    *,
    path: str = "DI_CONNECT/DI-Connect-Wellness/sleepData.json",
    media_type: str = "application/json",
) -> SourceDocument:
    return SourceDocument(
        evidence_id="evidence-1",
        source_path=path,
        media_type=media_type,
        checksum="abc123",
        payload={},
    )


def test_register_returns_new_registry_without_mutating_original() -> None:
    empty = ParserRegistry()
    populated = empty.register(FakeParser(name="sleep"))

    assert empty.parsers == ()
    assert len(populated.parsers) == 1


def test_registry_matches_path_and_media_type() -> None:
    registry = ParserRegistry().register(FakeParser(name="sleep"))

    matches = registry.matching(source_document())

    assert len(matches) == 1
    assert matches[0].parser.name == "sleep"


def test_registry_rejects_wrong_media_type() -> None:
    registry = ParserRegistry().register(FakeParser(name="sleep"))

    assert registry.matching(source_document(media_type="text/csv")) == ()
    assert registry.parse(source_document(media_type="text/csv")) is None


def test_registry_rejects_duplicate_parser_name() -> None:
    registry = ParserRegistry().register(FakeParser(name="sleep"))

    with pytest.raises(ValueError, match="already registered"):
        registry.register(FakeParser(name="sleep"))


def test_registry_rejects_ambiguous_match() -> None:
    registry = ParserRegistry(
        (
            FakeParser(name="sleep-a"),
            FakeParser(name="sleep-b"),
        )
    )

    with pytest.raises(ValueError, match="Multiple parsers match"):
        registry.parse(source_document())


def test_registry_returns_parser_result_with_provenance() -> None:
    registry = ParserRegistry().register(FakeParser(name="sleep"))

    result = registry.parse(source_document())

    assert result is not None
    assert result.parser_name == "sleep"
    assert result.source_evidence_id == "evidence-1"
    assert result.errors == ()
