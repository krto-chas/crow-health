from crow_health.live_sources import FeasibilityStatus, garmin_live_source_report


def test_recommends_only_official_health_api_for_future_automation() -> None:
    report = garmin_live_source_report()

    assert report.recommended_candidate_id == "garmin-health-api"
    candidate = next(
        item for item in report.candidates if item.candidate_id == report.recommended_candidate_id
    )
    assert candidate.official is True
    assert candidate.automated is True
    assert candidate.health_data is True
    assert candidate.oauth2 is True
    assert candidate.status is FeasibilityStatus.CONDITIONAL


def test_does_not_authorize_implementation_before_external_requirements() -> None:
    report = garmin_live_source_report()

    assert report.implementation_authorized is False
    assert len(report.blocking_requirements) >= 5
    assert any("approval" in item.lower() for item in report.blocking_requirements)
    assert any("raw" in item.lower() for item in report.blocking_requirements)


def test_rejects_undocumented_endpoints() -> None:
    report = garmin_live_source_report()
    candidate = next(
        item
        for item in report.candidates
        if item.candidate_id == "undocumented-connect-endpoints"
    )

    assert candidate.official is False
    assert candidate.status is FeasibilityStatus.NOT_RECOMMENDED


def test_report_is_deterministic_and_machine_readable() -> None:
    first = garmin_live_source_report().to_dict()
    second = garmin_live_source_report().to_dict()

    assert first == second
    assert first["report_version"] == "crow-health.garmin-live-feasibility.v1"
    assert len(first["official_sources"]) == 4
