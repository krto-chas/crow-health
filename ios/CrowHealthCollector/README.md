# Crow Health Collector — RC1 Pass 3

This folder contains the minimal source files for a physical-device SwiftUI/HealthKit collector.

## Purpose

The app requests read-only access to a deliberately limited HealthKit set and creates `crow-health.apple-health-manifest.v1`. The manifest contains counts, date coverage, units and source identities, but no health sample values.

## Xcode setup

1. Create a new iOS App target named `CrowHealthCollector` using SwiftUI and Swift.
2. Add the Swift files in this folder to the target.
3. Add the HealthKit capability under **Signing & Capabilities**.
4. Use `CrowHealthCollector.entitlements` or let Xcode generate the equivalent entitlement.
5. Add this privacy string to the target Info settings:

   `Privacy - Health Share Usage Description` (`NSHealthShareUsageDescription`)

   Suggested value: `Crow Health inventories the Health data types and sources you choose to share. This pass does not export measurement values.`

6. Select your Apple Developer team and a unique bundle identifier.
7. Run on a physical iPhone. HealthKit authorization and the real Garmin/Apple source inventory cannot be verified in the simulator.

## Expected workflow

1. Tap **Authorize and build manifest**.
2. Grant only the Health categories you approve.
3. Review the on-device counts and sources.
4. Share `apple_health_manifest.json`.
5. Validate the file in Crow Health using the RC1 Pass 2 manifest loader and coverage report.

## Evidence boundary

This collector does not upload data, store sample values, enable background delivery or create Crow Health observations. A successful Python CI run does not prove that this iOS source compiles or that HealthKit returns Garmin data. Those points require an Xcode build and a physical-device run.
