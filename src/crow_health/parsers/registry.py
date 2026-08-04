from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch
from typing import Any

from crow_health.parsers.contracts import ParserContract


@dataclass(frozen=True, slots=True)
class ParserMatch:
    parser: ParserContract
    source_path: str


class ParserRegistry:
    def __init__(self, parsers: tuple[ParserContract, ...] = ()) -> None:
        self._parsers = parsers

    def register(self, parser: ParserContract) -> "ParserRegistry":
        return ParserRegistry((*self._parsers, parser))

    def matching(self, source_path: str) -> tuple[ParserMatch, ...]:
        return tuple(
            ParserMatch(parser=parser, source_path=source_path)
            for parser in self._parsers
            if any(fnmatch(source_path, pattern) for pattern in parser.supported_path_patterns)
        )

    def parse(self, source_path: str, payload: dict[str, Any] | list[Any]) -> tuple[Any, ...]:
        matches = self.matching(source_path)
        if not matches:
            return ()
        if len(matches) > 1:
            names = ", ".join(match.parser.name for match in matches)
            raise ValueError(f"Multiple parsers match {source_path}: {names}")
        return tuple(matches[0].parser.parse(source_path, payload))
