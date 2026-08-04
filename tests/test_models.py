from datetime import UTC, datetime

from crow_health.evidence.models import Observation


def test_observation_preserves_missing_values() -> None:
    item = Observation(
        "o1",
        "e1",
        "file.json",
        "hrv",
        None,
        "ms",
        None,
        datetime.now(UTC),
        "test",
        "1",
    )
    assert item.value is None
    assert item.observed_at is None
