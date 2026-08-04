from crow_health.parsers.garmin_sleep import GarminSleepParser
from crow_health.parsers.registry import ParserRegistry


def default_parser_registry() -> ParserRegistry:
    return ParserRegistry().register(GarminSleepParser())
