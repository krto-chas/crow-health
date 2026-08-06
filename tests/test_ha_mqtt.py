from datetime import UTC, date, datetime

from crow_health.ha import HomeAssistantMqttAdapter
from crow_health.snapshot import PresentationSnapshot, SnapshotMetric


def snapshot() -> PresentationSnapshot:
    metric = SnapshotMetric(
        metric="sleep.score.overall",
        display_name="Overall sleep score",
        description="Overall Garmin sleep score.",
        category="sleep",
        value_type="integer",
        unit="score",
        observation_count=2,
        covered_days=2,
        first_observed_at=datetime(2026, 8, 1, tzinfo=UTC),
        last_observed_at=datetime(2026, 8, 2, tzinfo=UTC),
        minimum=80,
        maximum=90,
        mean=85,
        latest_day=date(2026, 8, 2),
        latest_value=90,
        moving_average=85,
        trend_direction="up",
        trend_difference=10,
        trend_percent_change=12.5,
        coverage_percent=100,
        expected_days=2,
        observed_days=2,
        missing_days=0,
        outlier_count=0,
    )
    return PresentationSnapshot(
        schema_version="crow-health.snapshot.v1",
        observed_from=None,
        observed_to=None,
        source_evidence_id=None,
        parser_name=None,
        moving_average_window_days=7,
        metrics=(metric,),
    )


def test_builds_discovery_and_state_messages() -> None:
    messages = HomeAssistantMqttAdapter().messages(snapshot())

    assert len(messages) == 2
    assert messages[0].topic == (
        "homeassistant/sensor/crow_health/sleep_score_overall/config"
    )
    assert '"unique_id": "crow_health_sleep_score_overall"' in messages[0].payload
    assert '"unit_of_measurement": "score"' in messages[0].payload
    assert messages[1].topic == "crow-health/crow_health/sleep_score_overall/state"
    assert '"value": 90' in messages[1].payload
    assert '"moving_average": 85' in messages[1].payload
    assert all(message.retain for message in messages)


def test_messages_are_deterministic() -> None:
    adapter = HomeAssistantMqttAdapter()
    assert adapter.messages(snapshot()) == adapter.messages(snapshot())


def test_custom_prefixes_and_device_id_are_normalized() -> None:
    messages = HomeAssistantMqttAdapter(
        discovery_prefix="ha/",
        state_prefix="health/",
        device_id="Crow Health VM",
    ).messages(snapshot())

    assert messages[0].topic.startswith("ha/sensor/crow_health_vm/")
    assert messages[1].topic.startswith("health/crow_health_vm/")
