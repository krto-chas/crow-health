from __future__ import annotations

from typing import Protocol

from crow_health.parsers.models import ParseResult, SourceDocument


class ParserContract(Protocol):
    name: str
    version: str
    supported_path_patterns: tuple[str, ...]
    supported_media_types: tuple[str, ...]

    def parse(self, document: SourceDocument) -> ParseResult: ...
