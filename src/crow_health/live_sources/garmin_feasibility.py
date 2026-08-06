from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any


class FeasibilityStatus(StrEnum):
    RECOMMENDED = "recommended"
    CONDITIONAL = "conditional"
    NOT_RECOMMENDED = "not_recommended"


@dataclass(frozen=True, slots=True)
class SourceCandidate:
    candidate_id: str
    name: str
    status: FeasibilityStatus
    official: bool
    automated: bool
    health_data: bool
    oauth2: bool
    approval_required: bool
    commercial_license_required: bool
    raw_evidence_available: bool
    notes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class GarminLiveSourceReport:
    report_version: str
    candidates: tuple[SourceCandidate, ...]
    recommended_candidate_id: str | None
    implementation_authorized: bool
    blocking_requirements: tuple[str, ...]
    official_sources: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def garmin_live_source_report() -> GarminLiveSourceReport:
    candidates = (
        SourceCandidate(
            candidate_id="garmin-health-api",
            name="Garmin Health API",
            status=FeasibilityStatus.CONDITIONAL,
            official=True,
            automated=True,
            health_data=True,
            oauth2=True,
            approval_required=True,
            commercial_license_required=True,
            raw_evidence_available=True,
            notes=(
                "Official cloud-to-cloud path for sleep, stress, heart rate, steps and other all-day health data.",
                "Access requires Garmin approval and an evaluation environment before production use.",
                "Commercial use requires a license fee.",
                "Supports push or ping/pull delivery after user consent and device sync.",
            ),
        ),
        SourceCandidate(
            candidate_id="garmin-account-export",
            name="Garmin account data export",
            status=FeasibilityStatus.RECOMMENDED,
            official=True,
            automated=False,
            health_data=True,
            oauth2=False,
            approval_required=False,
            commercial_license_required=False,
            raw_evidence_available=True,
            notes=(
                "Official user-initiated export and the current verified Crow Health ingestion route.",
                "Suitable for historical backfill and evidence preservation, not continuous freshness.",
                "Garmin states delivery may take from roughly 48 hours up to 30 days.",
            ),
        ),
        SourceCandidate(
            candidate_id="daily-wellness-fit-export",
            name="Daily wellness FIT export",
            status=FeasibilityStatus.CONDITIONAL,
            official=True,
            automated=False,
            health_data=True,
            oauth2=False,
            approval_required=False,
            commercial_license_required=False,
            raw_evidence_available=True,
            notes=(
                "Official manual export of one day of wellness FIT data.",
                "Contains wellness data such as sleep, stress and HRV according to Garmin support.",
                "Could support frequent manual updates but is not an unattended integration.",
            ),
        ),
        SourceCandidate(
            candidate_id="undocumented-connect-endpoints",
            name="Undocumented Garmin Connect endpoints",
            status=FeasibilityStatus.NOT_RECOMMENDED,
            official=False,
            automated=True,
            health_data=True,
            oauth2=False,
            approval_required=False,
            commercial_license_required=False,
            raw_evidence_available=False,
            notes=(
                "No official stability, authorization or compatibility contract was identified.",
                "Credential handling and endpoint changes would create operational and security risk.",
                "Excluded from RC1 unless Garmin publishes and supports the interface.",
            ),
        ),
    )
    return GarminLiveSourceReport(
        report_version="crow-health.garmin-live-feasibility.v1",
        candidates=candidates,
        recommended_candidate_id="garmin-health-api",
        implementation_authorized=False,
        blocking_requirements=(
            "Submit and obtain approval for the Garmin Connect Developer Program Health API.",
            "Obtain evaluation credentials and official API documentation.",
            "Confirm license terms and cost are acceptable for Crow Health.",
            "Verify sleep payload coverage against the existing normalized metric registry.",
            "Define OAuth 2.0 secret storage, consent, token rotation and revocation handling.",
            "Archive immutable raw API payloads before normalization.",
        ),
        official_sources=(
            "https://developer.garmin.com/gc-developer-program/health-api/",
            "https://developer.garmin.com/gc-developer-program/overview/",
            "https://developer.garmin.com/gc-developer-program/program-faq/",
            "https://support.garmin.com/en-US/?faq=W1TvTPW8JZ6LfJSfK512Q8",
        ),
    )
