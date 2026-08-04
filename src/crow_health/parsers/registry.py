from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch

from crow_health.parsers.contracts import ParserContract
from crow_health.parsers.models import ParseResult, SourceDocument


@dataclass(frozen=True, slots=True)
class ParserMatch:
    parser: ParserContract
    source_path: str


class ParserRegistry:
    def __init__(self, parsers: tuple[ParserContract, ...] = ()) -> None:
        self._parsers = parsers

    @property
    def parsers(self) -> tuple[ParserContract, ...]:
        return self._parsers

    def register(self, parser: ParserContract) -> "ParserRegistry":
        if any(existing.name == parser.name for existing in self._parsers):
            raise ValueError(f"Parser already registered: {parser.name}")
        return ParserRegistry((*self._parsers, parser))

    def matching(self, document: SourceDocument) -> tuple[ParserMatch, ...]:
        return tuple(
            ParserMatch(parser=parser, source_path=document.source_path)
            for parser in self._parsers
            if document.media_type in parser.supported_media_types
            and any(
                fnmatch(document.source_path, pattern)
                for pattern in parser.supported_path_patterns
            )
        )

    def parse(self, document: SourceDocument) -> ParseResult | None:
        matches = self.matching(document)
        if not matches:
            return None
        if len(matches) > 1:
            names = ", ".join(match.parser.name for match in matches)
            raise ValueError(f"Multiple parsers match {document.source_path}: {names}")
        return matches[0].parser.parse(document)
