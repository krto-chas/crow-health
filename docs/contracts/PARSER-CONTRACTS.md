# Initial parser contracts

These are contracts, not parser implementations.

| Parser | Observed Garmin source family | Intended output |
|---|---|---|
| Sleep | `DI-Connect-Wellness/*_sleepData.json` | Sleep-session observations |
| Daily summary | `DI-Connect-Aggregator/UDSFile_*.json` | Daily pulse, stress, steps and Body Battery observations where present |
| HRV | To be confirmed from observed export families/fields | HRV observations only after field semantics are verified |
| Training | `DI-Connect-Metrics/TrainingHistory_*.json` | Training-status/load observations |

No parser may infer units, timestamps or missing values.
