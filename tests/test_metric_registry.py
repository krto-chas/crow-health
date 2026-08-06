from datetime import UTC, datetime

import pytest

from crow_health.evidence.models import Observation
from crow_health.registry import (
    DuplicateMetricError,
    MetricDefinition,
    MetricRegistry,
    MetricValueType,
    UnknownMetricError,
    default_metric_registry,
)


def definition(metric: str) -> MetricDefinition:
    return MetricDefinition(
        metric=metric,
        display_name=metric,
        description="Synthetic test metric.",
        category="test",
        unit=None,
        value_type=MetricValueType.NUMBER,
        statistics_supported=True,
        analytics_supported=True,
    )


def observation(metric: str, value: object, unit: str | None = None) -> Observation:
    return Observation(
        observation_id="id",
        source_evidence_id="evidence",
        source_path="sample.json",
        metric=metric,
        value=value,
        unit=unit,
        observed_at=datetime(2026, 8, 6, tzinfo=UTC),
        imported_at=datetime(2026, 8, 6, tzinfo=UTC),
        parser_name="test",
        parser_version="1",
    )


def test_default_registry_is_sorted_and_complete_for_sleep_parser() -> None:
    definitions = default_metric_registry().list(category="sleep")

    assert len(definitions) == 27
    assert [item.metric for item in definitions] == sorted(
        item.metric for item in definitions
    )
    assert definitions[0].category == "sleep"


def test_lookup_and_exact_filter() -> None:
    registry = default_metric_registry()

    result = registry.list(metric="sleep.score.overall")

    assert result == (registry.get("sleep.score.overall"),)
    assert result[0].unit == "score"
    assert result[0].value_type is MetricValueType.INTEGER


def test_rejects_duplicate_definitions() -> None:
    with pytest.raises(DuplicateMetricError):
        MetricRegistry((definition("metric"), definition("metric")))


def test_unknown_metric_fails_closed() -> None:
    with pytest.raises(UnknownMetricError):
        default_metric_registry().get("missing")


def test_validates_observation_unit_and_type() -> None:
    registry = default_metric_registry()
    registry.validate_observations(
        (observation("sleep.score.overall", 80, "score"),)
    )

    with pytest.raises(ValueError, match="expected unit"):
        registry.validate_observations(
            (observation("sleep.score.overall", 80, None),)
        )
    with pytest.raises(TypeError, match="expected integer"):
        registry.validate_observations(
            (observation("sleep.score.overall", 80.5, "score"),)
        )
