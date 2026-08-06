# ADR-0022: Apple Health source contract before live collection

## Context

Crow Health needs a maintainable path for current data. Garmin Connect can write selected categories to Apple Health, while HealthKit provides user-authorized read access, source attribution, observer queries and background delivery on a physical iOS device.

Apple Health is not a complete mirror of Garmin. Garmin-specific sleep scores, Body Battery and other proprietary values may be absent. Multiple apps and devices may also contribute samples of the same HealthKit type.

Official references reviewed for this decision:

- Apple Developer Documentation: `HKHealthStore`
- Apple Developer Documentation: `HKObserverQuery` and observer-query execution
- Garmin Support: information shared from Garmin Connect to Apple Health

## Decision

Introduce a value-free, versioned Apple Health manifest contract before importing sample values.

The first iOS collector must report only:

- HealthKit type identifier
- source name and source bundle identifier
- number of accessible samples
- earliest and latest timestamps
- observed unit names

The server-side coverage service classifies each type as supported, partial or unsupported and preserves source attribution. It performs no unit conversion and creates no observations.

Sleep analysis is classified as partial because HealthKit sleep stages cannot be treated as equivalent to Garmin's proprietary sleep scores.

## Consequences

The next implementation pass can build a minimal HealthKit collector against a stable manifest schema and verify actual Garmin Connect coverage on the user's iPhone before any live upload endpoint is added.

Background-delivery behavior must be tested on a physical iPhone; the simulator is not accepted as evidence for background HealthKit collection.

No personal sample values, HealthKit authorization flow, server upload, checkpoint, background scheduling or new metric definitions are introduced by this pass.
