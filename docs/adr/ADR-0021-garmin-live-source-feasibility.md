# ADR-0021: Garmin live-source feasibility

## Status

Proposed for RC1 Pass 1.

## Context

RC0 can import historical Garmin account exports and expose verified observations through statistics, snapshots, the read-only API and Home Assistant. It does not have a supported unattended route for current Garmin health data.

The feasibility review uses official Garmin material only:

- Garmin Health API: https://developer.garmin.com/gc-developer-program/health-api/
- Garmin Connect Developer Program overview: https://developer.garmin.com/gc-developer-program/overview/
- Garmin Connect Developer Program FAQ: https://developer.garmin.com/gc-developer-program/program-faq/
- Garmin account and wellness export guidance: https://support.garmin.com/en-US/?faq=W1TvTPW8JZ6LfJSfK512Q8

Garmin states that its Health API exposes all-day health data including sleep, stress, heart rate and steps. The official route is cloud-to-cloud, uses OAuth 2.0, requires program approval and an evaluation environment, and requires a license fee for commercial use. Garmin also supports push and ping/pull delivery models after user consent and device synchronization.

Garmin's account export and daily wellness FIT export remain official routes for user-controlled evidence acquisition, but neither is an unattended continuous feed. The full account export can take roughly 48 hours and, according to Garmin support, up to 30 days.

No official contract was identified for scripting Garmin Connect's private web endpoints with account credentials.

## Decision

1. Treat the Garmin Health API as the only acceptable target for a future automated Garmin health-data adapter.
2. Keep implementation blocked until Crow Health has:
   - Garmin program approval;
   - evaluation credentials and official API documentation;
   - acceptable license terms;
   - verified sleep-payload coverage;
   - an OAuth 2.0 credential and consent design;
   - immutable raw-payload archiving before normalization.
3. Continue using account exports for historical backfill and evidence verification.
4. Allow daily wellness FIT export as a manual interim path, but do not describe it as live synchronization.
5. Do not implement or depend on undocumented Garmin Connect endpoints.

## Consequences

- RC1 Pass 1 produces a deterministic feasibility report and tests, not a live connector.
- Home Assistant freshness remains limited by the latest imported data.
- The next implementation pass depends on an external Garmin approval decision.
- A rejected or commercially unsuitable Garmin application means Crow Health must retain manual Garmin imports while prioritizing other supported sources such as Apple Health exports or approved vendor APIs.
