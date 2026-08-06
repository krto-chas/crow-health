from __future__ import annotations

from collections.abc import Iterable

from crow_health.evidence.models import Observation
from crow_health.registry.models import MetricDefinition, MetricValueType


class DuplicateMetricError(ValueError):
    pass


class UnknownMetricError(KeyError):
    pass


class MetricRegistry:
    def __init__(self, definitions: Iterable[MetricDefinition]) -> None:
        items: dict[str, MetricDefinition] = {}
        for definition in definitions:
            if definition.metric in items:
                raise DuplicateMetricError(f"Duplicate metric: {definition.metric}")
            items[definition.metric] = definition
        self._definitions = items

    def get(self, metric: str) -> MetricDefinition:
        try:
            return self._definitions[metric]
        except KeyError as exc:
            raise UnknownMetricError(metric) from exc

    def list(
        self,
        *,
        category: str | None = None,
        metric: str | None = None,
    ) -> tuple[MetricDefinition, ...]:
        definitions = self._definitions.values()
        if category is not None:
            definitions = (item for item in definitions if item.category == category)
        if metric is not None:
            definitions = (item for item in definitions if item.metric == metric)
        return tuple(sorted(definitions, key=lambda item: item.metric))

    def validate_observations(self, observations: Iterable[Observation]) -> None:
        for observation in observations:
            definition = self.get(observation.metric)
            if observation.unit != definition.unit:
                raise ValueError(
                    f"Metric {observation.metric} expected unit {definition.unit!r}, "
                    f"got {observation.unit!r}"
                )
            if not _matches_type(observation.value, definition.value_type):
                raise TypeError(
                    f"Metric {observation.metric} expected {definition.value_type.value}, "
                    f"got {type(observation.value).__name__}"
                )


def _matches_type(value: object, expected: MetricValueType) -> bool:
    if expected is MetricValueType.BOOLEAN:
        return isinstance(value, bool)
    if expected is MetricValueType.INTEGER:
        return isinstance(value, int) and not isinstance(value, bool)
    if expected is MetricValueType.NUMBER:
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(value, str)


def _metric(
    metric: str,
    display_name: str,
    description: str,
    unit: str | None,
    value_type: MetricValueType,
    *,
    statistics: bool = True,
    analytics: bool = True,
) -> MetricDefinition:
    return MetricDefinition(
        metric=metric,
        display_name=display_name,
        description=description,
        category="sleep",
        unit=unit,
        value_type=value_type,
        statistics_supported=statistics,
        analytics_supported=analytics,
    )


_DEFAULT_DEFINITIONS = (
    _metric("sleep.awake_seconds", "Awake time", "Awake time within the sleep session.", "s", MetricValueType.INTEGER),
    _metric("sleep.deep_seconds", "Deep sleep", "Deep-sleep duration.", "s", MetricValueType.INTEGER),
    _metric("sleep.light_seconds", "Light sleep", "Light-sleep duration.", "s", MetricValueType.INTEGER),
    _metric("sleep.rem_seconds", "REM sleep", "REM-sleep duration.", "s", MetricValueType.INTEGER),
    _metric("sleep.unmeasurable_seconds", "Unmeasurable sleep", "Duration Garmin could not classify.", "s", MetricValueType.INTEGER),
    _metric("sleep.awake_count", "Awake count", "Recorded awakenings.", "count", MetricValueType.INTEGER),
    _metric("sleep.restless_moment_count", "Restless moments", "Recorded restless moments.", "count", MetricValueType.INTEGER),
    _metric("sleep.average_stress", "Average sleep stress", "Average stress value during sleep.", None, MetricValueType.NUMBER),
    _metric("sleep.respiration.average", "Average respiration", "Average respiration during sleep.", None, MetricValueType.NUMBER),
    _metric("sleep.respiration.highest", "Highest respiration", "Highest respiration during sleep.", None, MetricValueType.NUMBER),
    _metric("sleep.respiration.lowest", "Lowest respiration", "Lowest respiration during sleep.", None, MetricValueType.NUMBER),
    _metric("sleep.retro", "Retrospective sleep", "Garmin retrospective-record flag.", None, MetricValueType.BOOLEAN, statistics=False, analytics=False),
    _metric("sleep.confirmation_type", "Confirmation type", "Garmin sleep-window confirmation type.", None, MetricValueType.STRING, statistics=False, analytics=False),
    _metric("sleep.score.overall", "Overall sleep score", "Overall Garmin sleep score.", "score", MetricValueType.INTEGER),
    _metric("sleep.score.quality", "Sleep quality score", "Garmin sleep-quality score.", "score", MetricValueType.INTEGER),
    _metric("sleep.score.recovery", "Recovery score", "Garmin recovery score.", "score", MetricValueType.INTEGER),
    _metric("sleep.score.duration", "Duration score", "Garmin sleep-duration score.", "score", MetricValueType.INTEGER),
    _metric("sleep.score.deep", "Deep sleep score", "Garmin deep-sleep score.", "score", MetricValueType.INTEGER),
    _metric("sleep.score.rem", "REM sleep score", "Garmin REM-sleep score.", "score", MetricValueType.INTEGER),
    _metric("sleep.score.light", "Light sleep score", "Garmin light-sleep score.", "score", MetricValueType.INTEGER),
    _metric("sleep.score.restfulness", "Restfulness score", "Garmin restfulness score.", "score", MetricValueType.INTEGER),
    _metric("sleep.score.awake_time", "Awake-time score", "Garmin awake-time score.", "score", MetricValueType.INTEGER),
    _metric("sleep.score.awakenings_count", "Awakenings score", "Garmin awakenings-count score.", "score", MetricValueType.INTEGER),
    _metric("sleep.score.combined_awake", "Combined awake score", "Garmin combined-awake score.", "score", MetricValueType.INTEGER),
    _metric("sleep.score.interruptions", "Interruptions score", "Garmin interruptions score.", "score", MetricValueType.INTEGER),
    _metric("sleep.score.feedback", "Sleep feedback", "Garmin sleep-score feedback text.", None, MetricValueType.STRING, statistics=False, analytics=False),
    _metric("sleep.score.insight", "Sleep insight", "Garmin sleep-score insight text.", None, MetricValueType.STRING, statistics=False, analytics=False),
)


def default_metric_registry() -> MetricRegistry:
    return MetricRegistry(_DEFAULT_DEFINITIONS)
