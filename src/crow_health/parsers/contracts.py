from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any, Protocol

from crow_health.evidence.models import Observation


class ParserContract(Protocol):
    name: str
    version: str
    supported_path_patterns: tuple[str, ...]

    def parse(self, source_path: str, payload: Mapping[str, Any] | list[Any]) -> Iterable[Observation]: ...
