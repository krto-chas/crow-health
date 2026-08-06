# ADR-0023: Collect Apple Health coverage before sample values

## Context

RC1 Pass 2 defined a value-free Apple Health manifest contract. The platform still lacks evidence about which HealthKit types and source applications are accessible on the user's physical iPhone, and whether Garmin Connect contributes the expected records.

## Decision

Build a minimal read-only SwiftUI collector that requests authorization for six reviewed HealthKit types and exports only aggregate inventory metadata: sample counts, first and last timestamps, units, source names and source bundle identifiers.

The collector must not export measurement values, upload data, create normalized observations, enable background delivery or claim that HealthKit is a complete Garmin mirror.

The source is stored without an Xcode project file. The project target, signing identity, capability and privacy description must be created in Xcode because they are tied to the user's Apple Developer configuration.

## Consequences

A physical-device run can provide the evidence needed to decide which Apple Health mappings should become production metrics. Python CI can continue to validate the server-side manifest contract, but it cannot verify the Swift source, code signing, HealthKit authorization or actual Garmin coverage. Those require a macOS/Xcode build and an iPhone run.
