from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from crow_health.evidence.models import Observation
from crow_health.storage import JsonlObservationIndex, JsonlObservationStore
from crow_health.timeline import ObservationTimeline, TimelineQuery


def observation(
    observation_id: str,
    metric: str,
    observed_at: datetime | None,
    *,
    evidence_id: str = "evidence-1",
    parser_name: str = "garmin-sleep",
) -> Observation:
    return Observation(
        observation_id=observation_id,
        source_evidence_id=evidence_id,
        source_path="sample.json",
        metric=metric,
        value=1,
        unit=None,
        observed_at=observed_at,
        imported_at=datetime(2026, 8, 5, tzinfo=UTC),
        parser_name=parser_name,
        parser_version="2",
    )


def timeline(tmp_path: Path, items: tuple[Observation, ...]) -> ObservationTimeline:
    store_path = tmp_path / "observations.jsonl"
    JsonlObservationStore(store_path).append(items)
    index = JsonlObservationIndex(store_path)
    index.rebuild()
    return ObservationTimeline(index)


def test_groups_same_session_and_sorts_metrics(tmp_path: Path) -> None:
    started_at = datetime(2026, 8, 1, 21, 30, tzinfo=UTC)
    result = timeline(
        tmp_path,
        (
            observation("2", "sleep.score.overall", started_at),
            observation("1", "sleep.deep_seconds", started_at),
        ),
    ).query(TimelineQuery())

    assert len(result.groups) == 1
    assert result.observation_count == 2
    assert [item.metric for item in result.groups[0].observations] == [
        "sleep.deep_seconds",
        "sleep.score.overall",
    ]


def test_orders_groups_by_observation_time(tmp_path: Path) -> None:
    result = timeline(
        tmp_path,
        (
            observation("later", "sleep.deep_seconds", datetime(2026, 8, 2, tzinfo=UTC)),
            observation("earlier", "sleep.deep_seconds", datetime(2026, 8, 1, tzinfo=UTC)),
        ),
    ).query(TimelineQuery())

    assert [group.observed_at.day for group in result.groups] == [1, 2]


def test_filters_by_utc_day_and_metric_prefix(tmp_path: Path) -> None:
    result = timeline(
        tmp_path,
        (
            observation("sleep", "sleep.deep_seconds", datetime(2026, 8, 1, 22, tzinfo=UTC)),
            observation("score", "sleep.score.overall", datetime(2026, 8, 1, 22, tzinfo=UTC)),
            observation("other", "sleep.deep_seconds", datetime(2026, 8, 2, 22, tzinfo=UTC)),
        ),
    ).query(TimelineQuery(day=date(2026, 8, 1), metric_prefix="sleep.score."))

    assert result.observation_count == 1
    assert result.groups[0].observations[0].observation_id == "score"


def test_separates_sources_with_same_timestamp(tmp_path: Path) -> None:
    observed_at = datetime(2026, 8, 1, 22, tzinfo=UTC)
    result = timeline(
        tmp_path,
        (
            observation("a", "sleep.deep_seconds", observed_at, evidence_id="source-a"),
            observation("b", "sleep.deep_seconds", observed_at, evidence_id="source-b"),
        ),
    ).query(TimelineQuery())

    assert len(result.groups) == 2
    assert {group.source_evidence_id for group in result.groups} == {"source-a", "source-b"}


def test_reports_excluded_observations_without_timestamp(tmp_path: Path) -> None:
    result = timeline(
        tmp_path,
        (observation("missing", "manual.note", None),),
    ).query(TimelineQuery())

    assert result.groups == ()
    assert result.excluded_without_timestamp == 1


def test_day_cannot_be_combined_with_explicit_range(tmp_path: Path) -> None:
    view = timeline(tmp_path, ())

    with pytest.raises(ValueError, match="day cannot be combined"):
        view.query(
            TimelineQuery(
                day=date(2026, 8, 1),
                observed_from=datetime(2026, 8, 1, tzinfo=UTC),
            )
        )
