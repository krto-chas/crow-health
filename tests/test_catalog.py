from datetime import UTC, datetime
from pathlib import Path

from crow_health.catalog import CatalogQuery, ObservationCatalog
from crow_health.evidence.models import Observation
from crow_health.storage import JsonlObservationStore


def observation(
    observation_id: str,
    metric: str,
    value: float | str | bool | None,
    observed_at: datetime | None,
    *,
    unit: str | None = None,
    parser_name: str = "garmin-sleep",
    evidence_id: str = "evidence-1",
) -> Observation:
    return Observation(
        observation_id=observation_id,
        source_evidence_id=evidence_id,
        source_path="sample.json",
        metric=metric,
        value=value,
        unit=unit,
        observed_at=observed_at,
        imported_at=datetime(2026, 8, 5, tzinfo=UTC),
        parser_name=parser_name,
        parser_version="2",
    )


def catalog(tmp_path: Path, items: tuple[Observation, ...]) -> ObservationCatalog:
    store = JsonlObservationStore(tmp_path / "observations.jsonl")
    store.append(items)
    return ObservationCatalog(store)


def test_builds_deterministic_metric_inventory(tmp_path: Path) -> None:
    result = catalog(
        tmp_path,
        (
            observation(
                "b",
                "sleep.score.overall",
                80,
                datetime(2026, 8, 2, tzinfo=UTC),
                unit="score",
                evidence_id="evidence-2",
            ),
            observation(
                "a",
                "sleep.average_stress",
                20,
                datetime(2026, 8, 1, tzinfo=UTC),
            ),
            observation(
                "c",
                "sleep.score.overall",
                90,
                datetime(2026, 8, 3, tzinfo=UTC),
                unit="score",
            ),
        ),
    ).build()

    assert result.metric_count == 2
    assert result.observation_count == 3
    assert [entry.metric for entry in result.metrics] == [
        "sleep.average_stress",
        "sleep.score.overall",
    ]
    score = result.metrics[1]
    assert score.observation_count == 2
    assert score.covered_days == 2
    assert score.source_evidence_count == 2
    assert score.value_types == ("number",)
    assert score.units == ("score",)
    assert score.statistics_supported is True


def test_reports_non_numeric_and_missing_timestamp_without_coercion(
    tmp_path: Path,
) -> None:
    result = catalog(
        tmp_path,
        (
            observation("text", "manual.note", "hello", None),
            observation("bool", "manual.note", True, None),
        ),
    ).build()

    entry = result.metrics[0]
    assert entry.timestamped_count == 0
    assert entry.first_observed_at is None
    assert entry.last_observed_at is None
    assert entry.value_types == ("boolean", "string")
    assert entry.numeric_observation_count == 0
    assert entry.statistics_supported is False


def test_mixed_units_disable_statistics_support(tmp_path: Path) -> None:
    result = catalog(
        tmp_path,
        (
            observation("a", "metric", 1, datetime(2026, 8, 1, tzinfo=UTC), unit="s"),
            observation("b", "metric", 2, datetime(2026, 8, 2, tzinfo=UTC), unit="ms"),
        ),
    ).build()

    assert result.metrics[0].units == ("ms", "s")
    assert result.metrics[0].statistics_supported is False


def test_filters_by_prefix_parser_and_source(tmp_path: Path) -> None:
    view = catalog(
        tmp_path,
        (
            observation("a", "sleep.score.overall", 80, datetime(2026, 8, 1, tzinfo=UTC)),
            observation(
                "b",
                "heart.rate",
                60,
                datetime(2026, 8, 1, tzinfo=UTC),
                parser_name="other",
                evidence_id="evidence-2",
            ),
        ),
    )

    result = view.build(
        CatalogQuery(
            metric_prefix="heart.",
            parser_name="other",
            source_evidence_id="evidence-2",
        )
    )

    assert result.metric_count == 1
    assert result.metrics[0].metric == "heart.rate"


def test_empty_store_returns_empty_catalog(tmp_path: Path) -> None:
    result = catalog(tmp_path, ()).build()

    assert result.metrics == ()
    assert result.metric_count == 0
    assert result.observation_count == 0
