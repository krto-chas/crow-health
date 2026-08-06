from __future__ import annotations

from collections.abc import Iterable

from crow_health.apple_health.models import (
    AppleHealthCoverageEntry,
    AppleHealthCoverageReport,
    AppleHealthManifestEntry,
    AppleHealthSupport,
    AppleHealthTypeDefinition,
)

APPLE_HEALTH_COVERAGE_SCHEMA = "crow-health.apple-health-coverage.v1"


_DEFINITIONS = (
    AppleHealthTypeDefinition(
        identifier="HKCategoryTypeIdentifierSleepAnalysis",
        crow_metric=None,
        support=AppleHealthSupport.PARTIAL,
        expected_unit=None,
        notes="Sleep stages can be inventoried, but Garmin sleep scores are not represented.",
    ),
    AppleHealthTypeDefinition(
        identifier="HKQuantityTypeIdentifierHeartRate",
        crow_metric="heart_rate.bpm",
        support=AppleHealthSupport.SUPPORTED,
        expected_unit="count/min",
        notes="Source attribution must be preserved because multiple devices may contribute.",
    ),
    AppleHealthTypeDefinition(
        identifier="HKQuantityTypeIdentifierRestingHeartRate",
        crow_metric="heart_rate.resting_bpm",
        support=AppleHealthSupport.SUPPORTED,
        expected_unit="count/min",
        notes="HealthKit-calculated or source-provided resting heart rate.",
    ),
    AppleHealthTypeDefinition(
        identifier="HKQuantityTypeIdentifierStepCount",
        crow_metric="activity.steps",
        support=AppleHealthSupport.SUPPORTED,
        expected_unit="count",
        notes="Aggregation and source precedence must be handled before observation import.",
    ),
    AppleHealthTypeDefinition(
        identifier="HKQuantityTypeIdentifierActiveEnergyBurned",
        crow_metric="energy.active_kcal",
        support=AppleHealthSupport.SUPPORTED,
        expected_unit="kcal",
        notes="No conversion is performed in the coverage pass.",
    ),
    AppleHealthTypeDefinition(
        identifier="HKQuantityTypeIdentifierBodyMass",
        crow_metric="body.weight_kg",
        support=AppleHealthSupport.SUPPORTED,
        expected_unit="kg",
        notes="No conversion is performed in the coverage pass.",
    ),
)


class AppleHealthCoverageService:
    def __init__(
        self,
        definitions: Iterable[AppleHealthTypeDefinition] = _DEFINITIONS,
    ) -> None:
        self._definitions = {item.identifier: item for item in definitions}

    def build(
        self,
        entries: Iterable[AppleHealthManifestEntry],
    ) -> AppleHealthCoverageReport:
        coverage = tuple(
            sorted(
                (self._entry(item) for item in entries),
                key=lambda item: (item.identifier, item.source_bundle_id),
            )
        )
        return AppleHealthCoverageReport(
            schema_version=APPLE_HEALTH_COVERAGE_SCHEMA,
            entries=coverage,
            supported_entry_count=sum(
                item.support is AppleHealthSupport.SUPPORTED for item in coverage
            ),
            partial_entry_count=sum(
                item.support is AppleHealthSupport.PARTIAL for item in coverage
            ),
            unsupported_entry_count=sum(
                item.support is AppleHealthSupport.UNSUPPORTED for item in coverage
            ),
            garmin_source_entry_count=sum(_is_garmin(item) for item in coverage),
        )

    def _entry(self, item: AppleHealthManifestEntry) -> AppleHealthCoverageEntry:
        definition = self._definitions.get(item.identifier)
        if definition is None:
            definition = AppleHealthTypeDefinition(
                identifier=item.identifier,
                crow_metric=None,
                support=AppleHealthSupport.UNSUPPORTED,
                expected_unit=None,
                notes="No reviewed Crow Health mapping exists for this HealthKit type.",
            )
        return AppleHealthCoverageEntry(
            identifier=item.identifier,
            crow_metric=definition.crow_metric,
            support=definition.support,
            source_bundle_id=item.source_bundle_id,
            source_name=item.source_name,
            sample_count=item.sample_count,
            earliest_sample=item.earliest_sample,
            latest_sample=item.latest_sample,
            observed_units=item.observed_units,
            expected_unit=definition.expected_unit,
            unit_matches=_unit_matches(item.observed_units, definition.expected_unit),
            notes=definition.notes,
        )


def _unit_matches(observed: tuple[str, ...], expected: str | None) -> bool | None:
    if expected is None or not observed:
        return None
    return observed == (expected,)


def _is_garmin(item: AppleHealthCoverageEntry) -> bool:
    value = f"{item.source_bundle_id} {item.source_name}".lower()
    return "garmin" in value
